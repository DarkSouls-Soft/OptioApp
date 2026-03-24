from __future__ import annotations

import numpy as np
from scipy.stats import norm

from app.domain.option_pricing import validate_option_params
from app.models import GreeksResult, OptionParams


def calculate_greeks(params: OptionParams) -> GreeksResult:
    validate_option_params(params)

    d1 = (
        np.log(params.spot / params.strike)
        + (params.risk_free_rate + 0.5 * params.volatility**2) * params.time_to_expiration
    ) / (params.volatility * np.sqrt(params.time_to_expiration))
    d2 = d1 - params.volatility * np.sqrt(params.time_to_expiration)

    delta = norm.cdf(d1) if params.option_type == "call" else -norm.cdf(-d1)
    gamma = norm.pdf(d1) / (params.spot * params.volatility * np.sqrt(params.time_to_expiration))

    if params.option_type == "call":
        theta = (
            -params.spot * norm.pdf(d1) * params.volatility / (2 * np.sqrt(params.time_to_expiration))
            - params.risk_free_rate
            * params.strike
            * np.exp(-params.risk_free_rate * params.time_to_expiration)
            * norm.cdf(d2)
        ) / 365.25
        rho = (
            params.strike
            * params.time_to_expiration
            * np.exp(-params.risk_free_rate * params.time_to_expiration)
            * norm.cdf(d2)
        ) * 0.01
    else:
        theta = (
            -params.spot * norm.pdf(d1) * params.volatility / (2 * np.sqrt(params.time_to_expiration))
            + params.risk_free_rate
            * params.strike
            * np.exp(-params.risk_free_rate * params.time_to_expiration)
            * norm.cdf(-d2)
        ) / 365.25
        rho = (
            -params.strike
            * params.time_to_expiration
            * np.exp(-params.risk_free_rate * params.time_to_expiration)
            * norm.cdf(-d2)
        ) * 0.01

    vega = params.spot * norm.pdf(d1) * np.sqrt(params.time_to_expiration) * 0.01
    return GreeksResult(
        delta=float(delta),
        gamma=float(gamma),
        theta=float(theta),
        vega=float(vega),
        rho=float(rho),
    )


def greek_curve(params: OptionParams, graph_parameter: str, greek_name: str, points: int = 150) -> tuple[np.ndarray, np.ndarray, str, float]:
    validate_option_params(params)
    greek_name = greek_name.lower()

    if graph_parameter == "volatility":
        x_values = np.linspace(0.01, max(1.0, params.volatility * 2), points)
        curve_label = "Volatility"
        curve_results = [
            calculate_greeks(
                OptionParams(
                    spot=params.spot,
                    strike=params.strike,
                    time_to_expiration=params.time_to_expiration,
                    risk_free_rate=params.risk_free_rate,
                    volatility=float(volatility),
                    option_type=params.option_type,
                )
            )
            for volatility in x_values
        ]
    else:
        x_values = np.linspace(0.5 * params.spot, 1.5 * params.spot, points)
        curve_label = "Price of the Underlying Asset"
        curve_results = [
            calculate_greeks(
                OptionParams(
                    spot=float(spot),
                    strike=params.strike,
                    time_to_expiration=params.time_to_expiration,
                    risk_free_rate=params.risk_free_rate,
                    volatility=params.volatility,
                    option_type=params.option_type,
                )
            )
            for spot in x_values
        ]

    y_values = np.array([getattr(result, greek_name) for result in curve_results], dtype=float)
    current_value = getattr(calculate_greeks(params), greek_name)
    return x_values, y_values, curve_label, current_value
