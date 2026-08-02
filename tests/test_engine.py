"""Ground-truth engine tests.

Every series here has an answer computable by hand. Real market data cannot do this —
a wrong answer on real data looks like a plausible answer, which is how engine bugs
survive to month six.
"""

from tr.engine.backtest import Strategy, bars_from_prices, run
from tr.engine.costs import CostModel, ZeroCost
from tr.types import MES, Bar, Session

FREE = ZeroCost()
COST = CostModel(contract=MES)


class AlwaysLong:
    def on_bar(self, bar: Bar) -> int:
        return 1


class AlwaysFlat:
    def on_bar(self, bar: Bar) -> int:
        return 0


def _run(prices: list[float], strategy: Strategy, costs: object = FREE):
    return run(bars_from_prices(prices), strategy, costs, MES)  # type: ignore[arg-type]


def test_constant_price_produces_exactly_zero_pnl() -> None:
    result = _run([100.0] * 20, AlwaysLong())
    assert result.net_pnl == 0.0


def test_flat_strategy_never_trades() -> None:
    result = _run([100.0, 105.0, 95.0, 110.0], AlwaysFlat())
    assert result.trades == []
    assert result.net_pnl == 0.0
    assert result.total_cost == 0.0


def test_linear_ramp_pnl_equals_points_times_multiplier() -> None:
    # Enters at bar 1's open (101), exits at final close (110) = 9 points x $5.
    result = _run([100.0 + i for i in range(11)], AlwaysLong())
    assert result.net_pnl == 45.0


def test_constant_price_with_costs_loses_exactly_one_round_trip() -> None:
    result = _run([100.0] * 10, AlwaysLong(), COST)
    assert abs(result.net_pnl + 2 * COST.per_side(Session.RTH)) < 1e-9


def test_signal_fills_at_next_bar_open_not_current_close() -> None:
    """A target set on bar i's close must fill at bar i+1's OPEN. If this ever
    regresses to same-bar fills, every backtest in the repo silently inflates."""
    bars = [
        Bar(ts=0, open=100.0, high=100.0, low=100.0, close=100.0, volume=1.0),
        Bar(ts=1, open=200.0, high=200.0, low=200.0, close=200.0, volume=1.0),
        Bar(ts=2, open=200.0, high=200.0, low=200.0, close=200.0, volume=1.0),
    ]
    result = run(bars, AlwaysLong(), FREE, MES)
    assert result.trades[0].entry_price == 200.0


def test_gross_minus_cost_equals_net() -> None:
    result = _run([100.0 + i for i in range(11)], AlwaysLong(), COST)
    assert abs(result.gross_pnl - result.total_cost - result.net_pnl) < 1e-9
    assert abs(result.gross_pnl - 45.0) < 1e-9


def test_equity_is_recorded_once_per_bar() -> None:
    prices = [100.0 + i for i in range(11)]
    result = _run(prices, AlwaysLong())
    assert len(result.equity) == len(prices)
    assert len(result.timestamps) == len(prices)
