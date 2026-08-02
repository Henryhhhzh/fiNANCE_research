# SEALED HOLDOUT — DO NOT TOUCH

**Range:** 2025-07-01 → 2026-07-31

This data is opened **exactly once**, in Phase 4 (stress test S8), after every other test has passed
and after the expected result has been written down.

The loader refuses to read this directory unless `I_AM_RUNNING_THE_FINAL_TEST=1` is set.

If it is tested more than once, the second result is worthless — the data is no longer out-of-sample,
and every number derived from it is a measurement of how well I remembered the first run. There is no
way to undo this. The only remedies are new data or waiting for time to pass.

Per GOAL.md §10, contaminating this holdout is a **hard stop** on the project.
