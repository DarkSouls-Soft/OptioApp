from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OptionType = Literal["call", "put"]
GraphParameter = Literal["underlying_price", "volatility"]
SimulationMethod = Literal["gbm", "jump_diffusion", "cir"]


@dataclass(frozen=True)
class OptionParams:
    spot: float
    strike: float
    time_to_expiration: float
    risk_free_rate: float
    volatility: float
    option_type: OptionType


@dataclass(frozen=True)
class GreeksResult:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass(frozen=True)
class JumpDiffusionEstimate:
    lambda_: float
    k: float
    delta: float
    diffusive_mu: float
    diffusive_sigma: float
    jump_count: int
    threshold: float


@dataclass(frozen=True)
class CIREstimate:
    kappa: float
    theta: float
    sigma: float
    method: str


@dataclass(frozen=True)
class TimeSeriesMetrics:
    mu: float
    sigma: float
    last_price: float
    periods_per_year: float
    annualization_source: str
    observations: int
    jump_params: JumpDiffusionEstimate
    cir_params: CIREstimate


@dataclass(frozen=True)
class MonteCarloBaseParams:
    initial_price: float
    mu: float
    sigma: float
    time_horizon: float
    steps: int
    num_tracks: int


@dataclass(frozen=True)
class JumpDiffusionParams(MonteCarloBaseParams):
    lambda_: float
    k: float
    delta: float


@dataclass(frozen=True)
class CIRParams(MonteCarloBaseParams):
    kappa: float
    theta: float


@dataclass(frozen=True)
class SimulationSummary:
    average_last_price: float
    last_prices: list[float]
