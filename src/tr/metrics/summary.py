import math

from tr.metrics.core import (
    Metrics,
    deflated_sharpe,
    longest_flat_periods,
    max_drawdown,
    periods_positive,
    profit_factor,
    return_concentration,
    returns_from_equity,
    sharpe,
    sortino,
)
from tr.types import Result

TRADING_DAYS = 252.0


def compute(
    result: Result,
    capital: float,
    periods_per_year: float = TRADING_DAYS,
    n_trials: int = 1,
) -> Metrics:
    returns = returns_from_equity(result.equity, capital)
    years = max(returns.size / periods_per_year, 1e-9)

    final = capital + result.net_pnl
    cagr = (final / capital) ** (1 / years) - 1 if final > 0 else -1.0

    dd = max_drawdown(result.equity, capital)
    sr = sharpe(returns, periods_per_year)
    probability, pvalue = deflated_sharpe(returns, n_trials)

    return Metrics(
        sharpe=sr,
        sortino=sortino(returns, periods_per_year),
        calmar=cagr / dd if dd > 0 else 0.0,
        cagr=cagr,
        volatility=float(returns.std(ddof=1) * math.sqrt(periods_per_year))
        if returns.size > 1
        else 0.0,
        max_drawdown=dd,
        profit_factor=profit_factor(result.trades),
        periods_positive=periods_positive(returns, max(1, int(periods_per_year // 12))),
        n_trades=len(result.trades),
        longest_flat_years=longest_flat_periods(result.equity, capital) / periods_per_year,
        concentration=return_concentration(result.trades),
        dsr_probability=probability,
        dsr_pvalue=pvalue,
        total_cost=result.total_cost,
        n_trials=n_trials,
    )
