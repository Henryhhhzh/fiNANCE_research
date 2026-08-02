import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats

from tr.types import Trade

EULER_MASCHERONI = 0.5772156649


def returns_from_equity(equity: Sequence[float], capital: float) -> np.ndarray:
    """Return on allocated capital. Futures P&L curves start at zero, so percentage
    returns are undefined without stating the capital the strategy is sized against."""
    if capital <= 0:
        raise ValueError("capital must be positive to express P&L as a return")
    return np.diff(np.asarray(equity, dtype=float)) / capital


def _is_flat(values: np.ndarray) -> bool:
    """Constant series. Compared relative to scale, not against exact zero: a
    hardcoded `std == 0.0` misses float noise around 1e-19 and lets Sharpe explode
    to ~1e16 on a series that never actually moved."""
    if values.size < 2:
        return True
    scale = float(np.abs(values).max())
    return bool(values.std(ddof=1) <= max(scale, 1.0) * 1e-9)


def sharpe(returns: np.ndarray, periods_per_year: float) -> float:
    if _is_flat(returns):
        return 0.0
    return float(returns.mean() / returns.std(ddof=1) * math.sqrt(periods_per_year))


def sortino(returns: np.ndarray, periods_per_year: float) -> float:
    downside = returns[returns < 0]
    if _is_flat(downside):
        return 0.0
    return float(returns.mean() / downside.std(ddof=1) * math.sqrt(periods_per_year))


def drawdown_curve(equity: Sequence[float], capital: float) -> np.ndarray:
    total = capital + (np.asarray(equity, dtype=float) - float(equity[0]))
    peak = np.maximum.accumulate(total)
    return (peak - total) / peak


def max_drawdown(equity: Sequence[float], capital: float) -> float:
    return float(drawdown_curve(equity, capital).max())


def longest_flat_periods(equity: Sequence[float], capital: float) -> int:
    """Longest run spent below a prior equity peak. This is the number that decides
    whether you can psychologically hold the strategy, per GOAL.md §1.1."""
    underwater = drawdown_curve(equity, capital) > 0
    longest = current = 0
    for below in underwater:
        current = current + 1 if below else 0
        longest = max(longest, current)
    return longest


def profit_factor(trades: Sequence[Trade]) -> float:
    wins = sum(t.net for t in trades if t.net > 0)
    losses = -sum(t.net for t in trades if t.net < 0)
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return wins / losses


def return_concentration(trades: Sequence[Trade], top_fraction: float = 0.05) -> float:
    """Share of total net P&L delivered by the best `top_fraction` of trades.
    A high value means the result is a lottery ticket wearing a strategy's clothes."""
    nets = sorted((t.net for t in trades), reverse=True)
    total = sum(nets)
    if not nets or total <= 0:
        return 0.0
    k = max(1, math.ceil(len(nets) * top_fraction))
    return sum(nets[:k]) / total


def periods_positive(returns: np.ndarray, periods_per_chunk: int) -> float:
    """Fraction of chunks with positive P&L. Calendar months once real timestamps
    are wired in; fixed-size chunks until then."""
    if periods_per_chunk < 1 or returns.size < periods_per_chunk:
        return 0.0
    usable = returns[: returns.size - (returns.size % periods_per_chunk)]
    chunks = usable.reshape(-1, periods_per_chunk).sum(axis=1)
    return float((chunks > 0).mean())


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """Expected maximum Sharpe from `n_trials` independent attempts on zero-edge data.
    This is the bar a real edge has to clear (Bailey & Lopez de Prado)."""
    if n_trials < 2:
        return 0.0
    a = stats.norm.ppf(1.0 - 1.0 / n_trials)
    b = stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return math.sqrt(sr_variance) * ((1 - EULER_MASCHERONI) * a + EULER_MASCHERONI * b)


def deflated_sharpe(
    returns: np.ndarray, n_trials: int, sr_variance: float | None = None
) -> tuple[float, float]:
    """Returns (probability the edge is real, p-value).

    Corrects the observed Sharpe for how many configurations were tried, and for the
    skew and fat tails of the return distribution. Without an honest trial count from
    research/TRIALS.csv this number is fiction, which is why §6.2 exists.
    """
    n = returns.size
    if n < 3 or _is_flat(returns):
        return 0.0, 1.0

    observed = returns.mean() / returns.std(ddof=1)
    if sr_variance is None:
        sr_variance = 1.0 / n

    threshold = expected_max_sharpe(n_trials, sr_variance)
    skew = float(stats.skew(returns))
    kurt = float(stats.kurtosis(returns, fisher=False))

    denominator = 1.0 - skew * observed + (kurt - 1.0) / 4.0 * observed**2
    if denominator <= 0:
        return 0.0, 1.0

    z = (observed - threshold) * math.sqrt(n - 1) / math.sqrt(denominator)
    probability = float(stats.norm.cdf(z))
    return probability, 1.0 - probability


@dataclass(frozen=True, slots=True)
class Metrics:
    sharpe: float
    sortino: float
    calmar: float
    cagr: float
    volatility: float
    max_drawdown: float
    profit_factor: float
    periods_positive: float
    n_trades: int
    longest_flat_years: float
    concentration: float
    dsr_probability: float
    dsr_pvalue: float
    total_cost: float
    n_trials: int
