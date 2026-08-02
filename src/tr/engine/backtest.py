from collections.abc import Iterable, Sequence
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

    equity: list[float] = []
    timestamps: list[int] = []
    trades: list[Trade] = []

    open_ts = 0
    open_price = 0.0
    open_contracts = 0
    open_cost = 0.0

    for bar in bars:
        if pending != position:
            delta = pending - position
            was_flat = position == 0
            fill_cost = costs.on_fill(delta, bar.session)
            total_cost += fill_cost
            open_cost += fill_cost

            if was_flat:
                open_ts, open_price, open_contracts = bar.ts, bar.open, delta

            position, avg_price, pnl = _apply_fill(
                position, avg_price, delta, bar.open, multiplier
            )
            realized += pnl

            if position == 0 and open_contracts != 0:
                trades.append(
                    Trade(
                        entry_ts=open_ts,
                        exit_ts=bar.ts,
                        contracts=open_contracts,
                        entry_price=open_price,
                        exit_price=bar.open,
                        gross=pnl,
                        cost=open_cost,
                    )
                )
                open_contracts, open_cost = 0, 0.0

        unrealized = position * (bar.close - avg_price) * multiplier
        equity.append(starting_equity + realized + unrealized - total_cost)
        timestamps.append(bar.ts)

        pending = strategy.on_bar(bar)

    if position != 0:
        last = bars[-1]
        fill_cost = costs.on_fill(-position, last.session)
        total_cost += fill_cost
        open_cost += fill_cost
        _, _, pnl = _apply_fill(position, avg_price, -position, last.close, multiplier)
        realized += pnl
        trades.append(
            Trade(
                entry_ts=open_ts,
                exit_ts=last.ts,
                contracts=open_contracts,
                entry_price=open_price,
                exit_price=last.close,
                gross=pnl,
                cost=open_cost,
            )
        )
        equity[-1] = starting_equity + realized - total_cost

    return Result(
        equity=equity, timestamps=timestamps, trades=trades, total_cost=total_cost
    )


def bars_from_prices(
    prices: Sequence[float], session: Session = Session.RTH, start_ts: int = 0
) -> list[Bar]:
    """Flat bars where open == high == low == close. Ground-truth fixtures for tests."""
    return [
        Bar(ts=start_ts + i, open=p, high=p, low=p, close=p, volume=1.0, session=session)
        for i, p in enumerate(prices)
    ]
