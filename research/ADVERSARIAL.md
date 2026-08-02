# Adversarial review log

Stress test S11 (GOAL.md §7): the strongest possible case that my result is fake.

Every finding gets logged here with its resolution. An unresolved critical finding blocks the strategy
from advancing, regardless of how good the backtest looks.

## Standing suspects

Checked at every review, because these are the failures that don't announce themselves:

- [ ] Lookahead via indicator computed on the full series before splitting
- [ ] Absolute price levels computed on back-adjusted rather than raw contract prices (GOAL.md §4.2b)
- [ ] Roll dates chosen with hindsight; roll costs not charged
- [ ] Same-bar fills — signal computed on close, executed on that same close
- [ ] Costs modelled as a constant rather than per time-of-day
- [ ] Trial count in TRIALS.csv lower than reality, inflating the Deflated Sharpe
- [ ] Outlier bars silently dropped, deleting real crashes
- [ ] Survivorship in the event/session filter
- [ ] Parameter chosen on a spike rather than a plateau
- [ ] Result driven by a handful of trades (GOAL.md §1.1 concentration limit)

## Findings

| # | Date | Finding | Severity | Resolution |
|---|---|---|---|---|
| | | | | |
