"""PHASE 0 EXIT GATE (GOAL.md).

Until these pass, no backtest result from this repo means anything.
"""

import pytest

from tr.engine.backtest import bars_from_prices, run
from tr.engine.costs import ZeroCost
from tr.engine.lookahead import (
    LaggedMomentum,
    LookaheadDetected,
    PeekingStrategy,
    assert_no_lookahead,
    detect_lookahead,
    edge_tstat,
    random_walk,
)
from tr.types import MES, Bar


def test_detector_catches_the_cheating_strategy() -> None:
    """The gate. A planted bug must be caught, or the detector cannot be trusted
    to catch an accidental one."""
    with pytest.raises(LookaheadDetected):
        assert_no_lookahead(PeekingStrategy)


def test_cheater_scores_absurdly_high_on_noise() -> None:
    assert detect_lookahead(PeekingStrategy, n_bars=1000, seeds=(1,)) > 20.0


def test_honest_strategy_passes() -> None:
    """Negative control. A detector that flags everything is as useless as one
    that flags nothing."""
    assert assert_no_lookahead(LaggedMomentum) < 5.0


def test_honest_strategy_makes_nothing_on_a_random_walk() -> None:
    prices = random_walk(4000, seed=7)
    result = run(bars_from_prices(prices), LaggedMomentum(), ZeroCost(), MES)
    assert abs(edge_tstat(result)) < 3.0


def test_strategy_cannot_reach_future_bars_through_the_interface() -> None:
    """Structural check: on_bar receives a single frozen Bar with no reference to
    the series, so there is no attribute path from a bar to any other bar."""
    bar = Bar(ts=0, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)
    assert not any(
        isinstance(getattr(bar, name, None), (list, tuple, dict))
        for name in dir(bar)
        if not name.startswith("_")
    )
    with pytest.raises(AttributeError):
        bar.close = 2.0  # type: ignore[misc]


def test_detector_is_deterministic() -> None:
    """Fixed seeds. A gate that returns a different verdict each run is not a gate."""
    assert detect_lookahead(PeekingStrategy, n_bars=500, seeds=(3,)) == detect_lookahead(
        PeekingStrategy, n_bars=500, seeds=(3,)
    )
