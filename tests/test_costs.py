from tr.engine.costs import CostModel
from tr.types import MES, Session

COST = CostModel(contract=MES)


def test_per_side_matches_hand_computed_rth_cost() -> None:
    # 0.64 commission + (0.5 spread tick + 1.0 slippage tick) x $1.25 = 2.515
    assert COST.per_side(Session.RTH) == 2.515


def test_round_trip_is_about_five_dollars() -> None:
    round_trip = 2 * COST.per_side(Session.RTH)
    assert abs(round_trip - 5.00) < 0.05


def test_round_trip_is_one_index_point_on_mes() -> None:
    """The number that decides strategy shape: ~1.0 index point per round trip,
    which is why GOAL.md §5 rules out scalping and commits to >=15 point targets."""
    points = (2 * COST.per_side(Session.RTH)) / MES.multiplier
    assert abs(points - 1.0) < 0.02


def test_overnight_costs_more_than_rth() -> None:
    assert COST.per_side(Session.ETH) > COST.per_side(Session.RTH)


def test_scaling_is_linear_for_stress_test_s2() -> None:
    base = COST.per_side(Session.RTH)
    for factor in (1.0, 1.5, 2.0, 3.0, 5.0):
        assert COST.scaled(factor).per_side(Session.RTH) == base * factor


def test_scaled_returns_a_new_model() -> None:
    doubled = COST.scaled(2.0)
    assert COST.scale == 1.0
    assert doubled.scale == 2.0
