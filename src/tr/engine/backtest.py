from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from tr.types import Bar, Contract, Result, Session, Trade


class Strategy(Protocol):
    """Receives one bar at a time and returns a target position in contracts.

    The strategy is never handed the full series, so it cannot read ahead even by
    mistake. Any history it needs, it accumulates itself — which is also how it will
    behave in live trading, so the same code path serves both.
    """

    def on_bar(self, bar: Bar) -> int: ...


class CostLike(Protocol):
    def on_fill(self, contracts: int, session: Session) -> float: ...


@dataclass(slots=True)
class _Leg:
    """One round trip: flat (or a flip) until the position is fully closed.

    Legs exist because a strategy that flips +1 to -1 never passes through zero.
    Recording trades only at position == 0 loses every one of those round trips.
    """

    entry_ts: int = 0
    entry_price: float = 0.0
    contracts: int = 0
    realized: float = 0.0
    cost: float = field(default=0.0)

    @property
    def is_open(self) -> bool:
        return self.contracts != 0

    def to_trade(self, exit_ts: int, exit_price: float) -> Trade:
        return Trade(
            entry_ts=self.entry_ts,
            exit_ts=exit_ts,
            contracts=self.contracts,
            entry_price=self.entry_price,
            exit_price=exit_price,
            gross=self.realized,
            cost=self.cost,
        )


def _apply_fill(
    position: int, avg_price: float, delta: int, price: float, multiplier: float
) -> tuple[int, float, float]:
    new_position = position + delta
    if position == 0 or (position > 0) == (delta > 0):
        total = abs(position) + abs(delta)
        return new_position, (avg_price * abs(position) + price * abs(delta)) / total, 0.0

    closed = min(abs(delta), abs(position))
    direction = 1.0 if position > 0 else -1.0
    realized = closed * (price - avg_price) * multiplier * direction
    if new_position == 0:
        return 0, 0.0, realized
    if abs(delta) > abs(position):
        return new_position, price, realized
    return new_position, avg_price, realized


def run(
    bars: Iterable[Bar],
    strategy: Strategy,
    costs: CostLike,
    contract: Contract,
    starting_equity: float = 0.0,
) -> Result:
    """Event-driven loop. A target set on bar i's close is filled at bar i+1's open.

    There is no path by which the strategy sees a bar before it is executed against —
    that is the point of the streaming interface, and it is what test_lookahead.py verifies.
    """
    bars = list(bars)
    multiplier = contract.multiplier

    position = 0
    pending = 0
    avg_price = 0.0
    realized = 0.0
    total_cost = 0.0
    leg = _Leg()

    equity: list[float] = []
    timestamps: list[int] = []
    trades: list[Trade] = []

    for bar in bars:
        if pending != position:
            delta = pending - position
            fill_cost = costs.on_fill(delta, bar.session)
            total_cost += fill_cost
            per_contract = fill_cost / abs(delta)

            reducing = position != 0 and delta * position < 0
            closed_qty = min(abs(delta), abs(position)) if reducing else 0
            opening_qty = abs(delta) - closed_qty

            new_position, avg_price, pnl = _apply_fill(
                position, avg_price, delta, bar.open, multiplier
            )
            realized += pnl
            leg.realized += pnl
            leg.cost += closed_qty * per_contract

            if reducing and (new_position == 0 or opening_qty > 0):
                trades.append(leg.to_trade(bar.ts, bar.open))
                leg = _Leg()

            if opening_qty > 0:
                if leg.is_open:
                    leg.contracts = new_position
                    leg.entry_price = avg_price
                    leg.cost += opening_qty * per_contract
                else:
                    leg = _Leg(
                        entry_ts=bar.ts,
                        entry_price=bar.open,
                        contracts=new_position,
                        cost=opening_qty * per_contract,
                    )

            position = new_position

        unrealized = position * (bar.close - avg_price) * multiplier
        equity.append(starting_equity + realized + unrealized - total_cost)
        timestamps.append(bar.ts)

        pending = strategy.on_bar(bar)

    if position != 0:
        last = bars[-1]
        fill_cost = costs.on_fill(-position, last.session)
        total_cost += fill_cost
        _, _, pnl = _apply_fill(position, avg_price, -position, last.close, multiplier)
        realized += pnl
        leg.realized += pnl
        leg.cost += fill_cost
        trades.append(leg.to_trade(last.ts, last.close))
        equity[-1] = starting_equity + realized - total_cost

    return Result(equity=equity, timestamps=timestamps, trades=trades, total_cost=total_cost)


def bars_from_prices(
    prices: Sequence[float], session: Session = Session.RTH, start_ts: int = 0
) -> list[Bar]:
    """Flat bars where open == high == low == close. Ground-truth fixtures for tests."""
    return [
        Bar(ts=start_ts + i, open=p, high=p, low=p, close=p, volume=1.0, session=session)
        for i, p in enumerate(prices)
    ]
