"""Lookahead detection. GOAL.md Phase 0 exit gate.

The engine prevents lookahead structurally: `on_bar` hands the strategy one bar and
never the series. This module tests the claim behaviourally, by running a strategy on
pure random-walk data where no edge can exist. Anything that profits there is reading
the future.

`PeekingStrategy` is the positive control. It is deliberately broken and must always be
caught. If it ever stops being caught, the detector has a hole and every backtest in
this repo is suspect.
"""

from collections.abc import Callable, Sequence

import numpy as np

from tr.engine.backtest import Strategy, bars_from_prices, run
from tr.engine.costs import ZeroCost
from tr.types import MES, Bar, Result

StrategyFactory = Callable[[Sequence[float]], Strategy]

DEFAULT_THRESHOLD = 5.0


class LookaheadDetected(Exception):
    pass


class PeekingStrategy:
    """Reads the future. A target set on bar i fills at bar i+1's open and exits at
    bar i+2's open, so knowing prices[i+2] is a perfect edge."""

    def __init__(self, prices: Sequence[float]) -> None:
        self._prices = list(prices)
        self._i = -1

    def on_bar(self, bar: Bar) -> int:
        self._i += 1
        if self._i + 2 >= len(self._prices):
            return 0
        return 1 if self._prices[self._i + 2] > self._prices[self._i + 1] else -1


class LaggedMomentum:
    """Negative control. Uses only bars it has already been shown, so on a random
    walk it must score ~0. If this ever trips the detector, the detector is too tight."""

    def __init__(self, prices: Sequence[float] | None = None) -> None:
        self._previous: float | None = None

    def on_bar(self, bar: Bar) -> int:
        signal = 0 if self._previous is None else (1 if bar.close > self._previous else -1)
        self._previous = bar.close
        return signal


def random_walk(n: int, seed: int, start: float = 5000.0, sigma: float = 1.0) -> list[float]:
    rng = np.random.default_rng(seed)
    return list(start + np.cumsum(rng.normal(0.0, sigma, n)))


def edge_tstat(result: Result) -> float:
    changes = np.diff(np.asarray(result.equity))
    if changes.size == 0 or changes.std() == 0.0:
        return 0.0
    return float(changes.mean() / changes.std() * np.sqrt(changes.size))


def detect_lookahead(
    factory: StrategyFactory, n_bars: int = 2000, seeds: Sequence[int] = (1, 2, 3)
) -> float:
    """Worst-case t-statistic across several random-walk realisations.

    Costs are zeroed deliberately: costs would mask a weak cheater, and this test is
    about information leakage, not profitability.
    """
    worst = 0.0
    for seed in seeds:
        prices = random_walk(n_bars, seed)
        result = run(bars_from_prices(prices), factory(prices), ZeroCost(), MES)
        worst = max(worst, abs(edge_tstat(result)))
    return worst


def assert_no_lookahead(
    factory: StrategyFactory, threshold: float = DEFAULT_THRESHOLD, **kwargs: object
) -> float:
    tstat = detect_lookahead(factory, **kwargs)  # type: ignore[arg-type]
    if tstat > threshold:
        raise LookaheadDetected(
            f"t-stat {tstat:.1f} on random-walk data exceeds {threshold}. "
            "No edge can exist in noise, so this strategy is reading the future."
        )
    return tstat
