import numpy as np

from tr.metrics.core import (
    deflated_sharpe,
    expected_max_sharpe,
    longest_flat_periods,
    max_drawdown,
    profit_factor,
    return_concentration,
    sharpe,
)
from tr.types import Trade


def _trade(net: float) -> Trade:
    return Trade(
        entry_ts=0, exit_ts=1, contracts=1, entry_price=0.0, exit_price=0.0, gross=net, cost=0.0
    )


def test_sharpe_matches_hand_computed_value() -> None:
    returns = np.array([0.01, -0.01] * 50)
    expected = returns.mean() / returns.std(ddof=1) * np.sqrt(252)
    assert abs(sharpe(returns, 252) - expected) < 1e-12


def test_zero_variance_returns_zero_not_infinity() -> None:
    assert sharpe(np.array([0.001] * 100), 252) == 0.0


def test_max_drawdown_matches_hand_computed_value() -> None:
    # equity 0 -> 100 -> 50 -> 200 on $1,000 capital; trough is 50 below a 1,100 peak.
    assert abs(max_drawdown([0.0, 100.0, 50.0, 200.0], 1000.0) - 50.0 / 1100.0) < 1e-12


def test_no_drawdown_on_monotonic_equity() -> None:
    assert max_drawdown([0.0, 1.0, 2.0, 3.0], 1000.0) == 0.0


def test_longest_flat_counts_periods_below_peak() -> None:
    assert longest_flat_periods([0.0, 10.0, 5.0, 6.0, 7.0, 20.0], 1000.0) == 3


def test_profit_factor_is_wins_over_losses() -> None:
    assert profit_factor([_trade(100), _trade(-50), _trade(50), _trade(-50)]) == 1.5


def test_concentration_flags_a_lottery_ticket() -> None:
    """One trade carrying everything is the failure GOAL.md §1.1 exists to catch."""
    trades = [_trade(1000.0)] + [_trade(1.0)] * 19
    assert return_concentration(trades, top_fraction=0.05) > 0.9


def test_concentration_is_low_when_pnl_is_spread_evenly() -> None:
    assert return_concentration([_trade(10.0)] * 100, top_fraction=0.05) < 0.10


def test_expected_max_sharpe_rises_with_trial_count() -> None:
    """The core of the Deflated Sharpe: the more configurations you try, the higher
    a Sharpe you should expect from pure luck."""
    variance = 1.0 / 1000
    assert (
        expected_max_sharpe(2, variance)
        < expected_max_sharpe(50, variance)
        < expected_max_sharpe(1000, variance)
    )


def test_more_trials_make_the_same_result_less_significant() -> None:
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0008, 0.01, 2000)
    _, p_one = deflated_sharpe(returns, n_trials=1)
    _, p_many = deflated_sharpe(returns, n_trials=500)
    assert p_many > p_one


def test_pure_noise_does_not_clear_the_deflated_bar() -> None:
    rng = np.random.default_rng(7)
    _, pvalue = deflated_sharpe(rng.normal(0.0, 0.01, 2000), n_trials=50)
    assert pvalue > 0.05
