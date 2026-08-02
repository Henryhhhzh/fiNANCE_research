# fiNANCE_research

Research harness for building and stress-testing a systematic trading strategy on CME micro equity
index futures (MES/MNQ), executed via Interactive Brokers.

The full plan, thresholds, and gates live in [GOAL.md](GOAL.md). Read that first — this repo exists to
serve it.

## Status

Phase 0 — infrastructure. No strategy work until the measurement apparatus is trustworthy.

**Phase 0 exit gate:** a deliberately-cheating strategy (one that reads tomorrow's close) must be
caught by `tests/test_lookahead.py`. Until that test passes, no backtest result from this repo means
anything.

## Layout

| Path | Contents |
|---|---|
| `src/tr/data/` | Download, load, hygiene assertions, continuous-contract roll builder |
| `src/tr/engine/` | Event loop, fill logic, cost model |
| `src/tr/strategy/` | `signal()` and `sizer()` — kept separate so costs and risk stay swappable |
| `src/tr/metrics/` | Sharpe, Deflated Sharpe, PBO, tearsheet |
| `src/tr/live/` | IBKR connection and position reconciliation |
| `research/` | Hypotheses, trial log, idea inbox, adversarial review |
| `data/` | Gitignored. Only `MANIFEST.txt` and the sealed-holdout README are tracked |

## Setup

```bash
uv sync
uv run pytest
```

## Rules this repo enforces

- `research/TRIALS.csv` records every configuration ever backtested. Deflated Sharpe is meaningless
  without an accurate count.
- `data/SEALED/` is opened exactly once, in Phase 4. See its README.
- Pass thresholds are committed to Git *before* the test that measures them runs. `git log` is the
  proof.
