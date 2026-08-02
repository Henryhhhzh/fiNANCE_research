from dataclasses import dataclass, replace

from tr.types import Contract, Session

IBKR_COMMISSION = 0.25
CME_EXCHANGE_FEE = 0.37
NFA_REGULATORY_FEE = 0.02


@dataclass(frozen=True, slots=True)
class CostModel:
    """Per-side execution cost. GOAL.md §5.

    `scale` is the multiplier stress test S2 sweeps over (1x, 1.5x, 2x, 3x, 5x).
    A strategy that dies between 1x and 1.5x was a cost-model artifact, not an edge.
    """

    contract: Contract
    commission_per_side: float = IBKR_COMMISSION + CME_EXCHANGE_FEE + NFA_REGULATORY_FEE
    spread_ticks_rth: float = 1.0
    spread_ticks_eth: float = 3.0
    slippage_ticks: float = 1.0
    scale: float = 1.0

    def per_side(self, session: Session) -> float:
        spread = self.spread_ticks_rth if session is Session.RTH else self.spread_ticks_eth
        crossing = (spread / 2 + self.slippage_ticks) * self.contract.tick_value
        return (self.commission_per_side + crossing) * self.scale

    def on_fill(self, contracts: int, session: Session) -> float:
        return abs(contracts) * self.per_side(session)

    def scaled(self, factor: float) -> "CostModel":
        return replace(self, scale=factor)


@dataclass(frozen=True, slots=True)
class ZeroCost:
    """Gross-only accounting. Used to isolate whether an edge is real before costs,
    and to prove the engine's arithmetic against hand-computed ground truth."""

    def on_fill(self, contracts: int, session: Session) -> float:
        return 0.0

    def scaled(self, factor: float) -> "ZeroCost":
        return self
