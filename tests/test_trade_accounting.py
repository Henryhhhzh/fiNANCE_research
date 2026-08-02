"""Trade accounting, including the flip case.

A strategy that reverses +1 to -1 never passes through flat. Recording trades only
when position hits zero silently loses every round trip, which shows up as
"Trades: 1" on a tearsheet for a strategy that traded hundreds of times.
"""

from tr.engine.backtest import bars_from_prices, run
from tr.engine.costs import ZeroCost
from tr.types import MES, Bar, Result

FREE = ZeroCost()


class Scripted:
    """Replays a fixed sequence of target positions, one per bar."""

    def __init__(self, targets: list[int]) -> None:
        self._targets = targets
        self._i = -1

    def on_bar(self, bar: Bar) -> int:
        self._i += 1
        return self._targets[self._i] if self._i < len(self._targets) else 0


def _run(prices: list[float], targets: list[int]) -> Result:
    return run(bars_from_prices(prices), Scripted(targets), FREE, MES)


def test_flip_records_two_trades_not_one() -> None:
    # long from bar 1, flip short at bar 3, flat at bar 5.
    result = _run([100.0, 101.0, 102.0, 103.0, 104.0, 105.0], [1, 1, -1, -1, 0, 0])
    assert len(result.trades) == 2
    assert result.trades[0].contracts == 1
    assert result.trades[1].contracts == -1


def test_flip_attributes_pnl_to_the_correct_leg() -> None:
    result = _run([100.0, 101.0, 102.0, 103.0, 104.0, 105.0], [1, 1, -1, -1, 0, 0])
    long_leg, short_leg = result.trades
    assert long_leg.gross == (103.0 - 101.0) * 5.0
    assert short_leg.gross == (103.0 - 105.0) * 5.0


def test_partial_reduction_keeps_the_leg_open() -> None:
    result = _run([100.0, 101.0, 102.0, 103.0, 104.0], [3, 3, 1, 0, 0])
    assert len(result.trades) == 1
    assert result.trades[0].contracts == 3


def test_round_trip_closes_the_leg() -> None:
    result = _run([100.0, 101.0, 102.0, 103.0], [1, 0, 0, 0])
    assert len(result.trades) == 1
    assert result.trades[0].exit_ts == 2


def test_trade_pnl_sums_to_total_net() -> None:
    result = _run([100.0, 105.0, 95.0, 110.0, 90.0, 100.0], [1, -1, 1, -1, 0, 0])
    assert abs(sum(t.net for t in result.trades) - result.net_pnl) < 1e-9


def test_alternating_strategy_records_many_trades() -> None:
    prices = [100.0 + (i % 7) for i in range(200)]
    targets = [1 if i % 2 == 0 else -1 for i in range(200)]
    result = _run(prices, targets)
    assert len(result.trades) > 50
