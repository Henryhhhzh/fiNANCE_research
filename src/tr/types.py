from dataclasses import dataclass
from enum import Enum


class Session(Enum):
    RTH = "RTH"
    ETH = "ETH"


@dataclass(frozen=True, slots=True)
class Contract:
    symbol: str
    multiplier: float
    tick_size: float

    @property
    def tick_value(self) -> float:
        return self.multiplier * self.tick_size


MES = Contract(symbol="MES", multiplier=5.0, tick_size=0.25)
MNQ = Contract(symbol="MNQ", multiplier=2.0, tick_size=0.25)


@dataclass(frozen=True, slots=True)
class Bar:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    session: Session = Session.RTH


@dataclass(frozen=True, slots=True)
class Trade:
    entry_ts: int
    exit_ts: int
    contracts: int
    entry_price: float
    exit_price: float
    gross: float
    cost: float

    @property
    def net(self) -> float:
        return self.gross - self.cost


@dataclass(frozen=True, slots=True)
class Result:
    equity: list[float]
    timestamps: list[int]
    trades: list[Trade]
    total_cost: float

    @property
    def net_pnl(self) -> float:
        return self.equity[-1] - self.equity[0]

    @property
    def gross_pnl(self) -> float:
        return self.net_pnl + self.total_cost
