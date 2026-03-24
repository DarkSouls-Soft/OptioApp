from __future__ import annotations

from typing import Iterable

import numpy as np
from scipy.stats import norm

from app.models import OptionParams


ALLOWED_OPTION_TYPES = {"call", "put"}


def validate_option_params(params: OptionParams) -> None:
    spot = np.asarray(params.spot)
    strike = np.asarray(params.strike)
    time_to_expiration = np.asarray(params.time_to_expiration)
    volatility = np.asarray(params.volatility)

    if np.any(spot <= 0):
        raise ValueError("Current asset price must be greater than 0.")
    if np.any(strike <= 0):
        raise ValueError("Strike price must be greater than 0.")
    if np.any(time_to_expiration <= 0):
        raise ValueError("Time to expiration must be greater than 0.")
    if np.any(volatility <= 0):
        raise ValueError("Volatility must be greater than 0.")
    if params.option_type not in ALLOWED_OPTION_TYPES:
        raise ValueError("Option type must be 'call' or 'put'.")


def _d1_d2(params: OptionParams) -> tuple[np.ndarray | float, np.ndarray | float]:
    d1 = (
        np.log(params.spot / params.strike)
        + (params.risk_free_rate + 0.5 * params.volatility**2) * params.time_to_expiration
    ) / (params.volatility * np.sqrt(params.time_to_expiration))
    d2 = d1 - params.volatility * np.sqrt(params.time_to_expiration)
    return d1, d2


def black_scholes_merton(params: OptionParams) -> np.ndarray | float:
    validate_option_params(params)
    d1, d2 = _d1_d2(params)

    if params.option_type == "call":
        return params.spot * norm.cdf(d1) - params.strike * np.exp(-params.risk_free_rate * params.time_to_expiration) * norm.cdf(d2)

    return params.strike * np.exp(-params.risk_free_rate * params.time_to_expiration) * norm.cdf(-d2) - params.spot * norm.cdf(-d1)


def option_price_curve(
    params: OptionParams,
    graph_parameter: str,
    points: int = 150,
) -> tuple[np.ndarray, np.ndarray, str]:
    validate_option_params(params)

    if graph_parameter == "volatility":
        x_values = np.linspace(0.01, max(1.0, params.volatility * 2), points)
        curve_params = OptionParams(
            spot=params.spot,
            strike=params.strike,
            time_to_expiration=params.time_to_expiration,
            risk_free_rate=params.risk_free_rate,
            volatility=x_values,
            option_type=params.option_type,
        )
        label = "Volatility"
    else:
        x_values = np.linspace(0.5 * params.spot, 1.5 * params.spot, points)
        curve_params = OptionParams(
            spot=x_values,
            strike=params.strike,
            time_to_expiration=params.time_to_expiration,
            risk_free_rate=params.risk_free_rate,
            volatility=params.volatility,
            option_type=params.option_type,
        )
        label = "Price of the Underlying Asset"

    y_values = black_scholes_merton(curve_params)
    return x_values, np.asarray(y_values), label
