"""Plain-text tearsheet. GOAL.md §1.1 thresholds, hard-coded.

Text rather than a dashboard on purpose: it diffs in git, greps across hundreds of
runs, and costs nothing to produce. A pretty equity curve invites you to look at the
nice green line and not notice the one metric that kills the idea.
"""

import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from tr.metrics.core import Metrics

MONTHS_PER_YEAR = 12


@dataclass(frozen=True, slots=True)
class Threshold:
    label: str
    value: Callable[[Metrics], float]
    limit: float
    higher_is_better: bool
    fmt: str = "{:.2f}"
    limit_fmt: str = "{:.2f}"

    def passes(self, m: Metrics) -> bool:
        v = self.value(m)
        return v >= self.limit if self.higher_is_better else v <= self.limit


THRESHOLDS: tuple[Threshold, ...] = (
    Threshold("Net Sharpe", lambda m: m.sharpe, 1.00, True),
    Threshold("Deflated Sharpe p", lambda m: m.dsr_pvalue, 0.05, False, "{:.3f}", "{:.3f}"),
    Threshold("Max drawdown", lambda m: m.max_drawdown * 100, 20.0, False, "{:.1f}%", "{:.1f}%"),
    Threshold("Calmar", lambda m: m.calmar, 0.75, True),
    Threshold("Profit factor", lambda m: m.profit_factor, 1.25, True),
    Threshold(
        "Periods positive", lambda m: m.periods_positive * 100, 55.0, True, "{:.1f}%", "{:.1f}%"
    ),
    Threshold("Trades", lambda m: m.n_trades, 200, True, "{:.0f}", "{:.0f}"),
    Threshold(
        "Longest flat",
        lambda m: m.longest_flat_years * MONTHS_PER_YEAR,
        9.0,
        False,
        "{:.1f}mo",
        "{:.1f}mo",
    ),
    Threshold(
        "Top-5% P&L share", lambda m: m.concentration * 100, 50.0, False, "{:.1f}%", "{:.1f}%"
    ),
)


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5
        )
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def tearsheet(
    metrics: Metrics,
    name: str,
    dataset: str,
    lookahead_status: str = "NOT RUN",
) -> str:
    """Defaults to NOT RUN, and NOT RUN fails the report.

    The cheating strategy passes all nine performance thresholds — lookahead makes
    every metric look excellent. So a default of "PASS" would mean a forgotten
    argument silently certifies the one check that matters.
    """
    lines = [
        f"STRATEGY  {name:<30}  COMMIT  {git_commit()}",
        f"DATA      {dataset:<30}  TRIALS  {metrics.n_trials}",
        f"COSTS     ${metrics.total_cost:,.2f} charged{'':<12}  LOOKAHEAD  {lookahead_status}",
        "",
        f"{'':<22}{'VALUE':>10}{'THRESH':>10}",
    ]

    failures = []
    for t in THRESHOLDS:
        value, ok = t.value(metrics), t.passes(metrics)
        comparator = "≥" if t.higher_is_better else ("<" if t.label.endswith("share") else "≤")
        marker = "PASS" if ok else "FAIL  ←"
        if not ok:
            failures.append(t.label)
        lines.append(
            f"{t.label:<22}{t.fmt.format(value):>10}"
            f"{comparator + t.limit_fmt.format(t.limit):>10}    {marker}"
        )

    if lookahead_status != "PASS":
        failures.insert(0, f"lookahead {lookahead_status}")

    lines += [
        "",
        f"CAGR {metrics.cagr * 100:.1f}%   Vol {metrics.volatility * 100:.1f}%   "
        f"Sortino {metrics.sortino:.2f}",
        f"Cost drag  ${metrics.total_cost:,.2f} total",
        "",
        f"OVERALL: {'PASS' if not failures else f'FAIL ({len(failures)})'}"
        + (f"  — {', '.join(failures)}" if failures else ""),
    ]
    return "\n".join(lines)
