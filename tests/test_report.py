from tr.engine.backtest import bars_from_prices, run
from tr.engine.costs import CostModel
from tr.engine.lookahead import LaggedMomentum, PeekingStrategy, random_walk
from tr.metrics.report import tearsheet
from tr.metrics.summary import compute
from tr.types import MES

PRICES = random_walk(2000, seed=11)


def _sheet(strategy: object, status: str = "PASS") -> str:
    result = run(bars_from_prices(PRICES), strategy, CostModel(contract=MES), MES)  # type: ignore[arg-type]
    metrics = compute(result, capital=25_000.0, n_trials=23)
    return tearsheet(metrics, "test", "synthetic", lookahead_status=status)


def test_cheater_clears_every_performance_threshold() -> None:
    """The reason the lookahead gate exists. A strategy reading the future looks
    excellent on all nine metrics — performance numbers cannot detect it."""
    assert "OVERALL: PASS" in _sheet(PeekingStrategy(PRICES))


def test_honest_strategy_on_noise_fails() -> None:
    assert "OVERALL: FAIL" in _sheet(LaggedMomentum())


def test_unrun_lookahead_check_fails_the_report() -> None:
    """A forgotten argument must never silently certify the gate."""
    sheet = _sheet(PeekingStrategy(PRICES), status="NOT RUN")
    assert "OVERALL: FAIL" in sheet
    assert "lookahead NOT RUN" in sheet


def test_report_names_the_failing_metrics() -> None:
    assert "Net Sharpe" in _sheet(LaggedMomentum())


def test_report_includes_commit_and_trial_count() -> None:
    sheet = _sheet(LaggedMomentum())
    assert "COMMIT" in sheet
    assert "TRIALS  23" in sheet
