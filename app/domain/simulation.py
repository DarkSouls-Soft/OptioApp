from __future__ import annotations

import numpy as np

from app.models import CIRParams, JumpDiffusionParams, MonteCarloBaseParams, SimulationSummary


def validate_simulation_params(params: MonteCarloBaseParams) -> None:
    if params.initial_price <= 0:
        raise ValueError("Initial asset price must be greater than 0.")
    if params.sigma < 0:
        raise ValueError("Volatility cannot be negative.")
    if params.time_horizon <= 0:
        raise ValueError("Time horizon must be greater than 0.")
    if params.steps <= 0:
        raise ValueError("Number of steps must be greater than 0.")
    if params.num_tracks <= 0:
        raise ValueError("Number of tracks must be greater than 0.")


def run_gbm_simulation(params: MonteCarloBaseParams) -> list[list[float]]:
    validate_simulation_params(params)
    dt = params.time_horizon / params.steps
    all_tracks: list[list[float]] = []

    for _ in range(params.num_tracks):
        price_paths = [params.initial_price]
        for _ in range(params.steps):
            shock = np.random.normal()
            price = price_paths[-1] * np.exp(
                (params.mu - 0.5 * params.sigma**2) * dt + params.sigma * np.sqrt(dt) * shock
            )
            price_paths.append(float(price))
        all_tracks.append(price_paths)

    return all_tracks


def run_jump_diffusion_simulation(params: JumpDiffusionParams) -> list[list[float]]:
    validate_simulation_params(params)
    if params.lambda_ < 0:
        raise ValueError("Lambda cannot be negative.")
    if params.delta < 0:
        raise ValueError("Delta cannot be negative.")

    dt = params.time_horizon / params.steps
    all_tracks: list[list[float]] = []

    for _ in range(params.num_tracks):
        price_paths = [params.initial_price]
        for _ in range(params.steps):
            jump_num = np.random.poisson(params.lambda_ * dt)
            jump_size = np.random.normal(params.k, params.delta, jump_num).sum() if jump_num else 0.0
            shock = np.random.normal()
            price = price_paths[-1] * np.exp(
                (params.mu - 0.5 * params.sigma**2) * dt
                + params.sigma * np.sqrt(dt) * shock
                + jump_size
            )
            price_paths.append(float(price))
        all_tracks.append(price_paths)

    return all_tracks


def run_cir_simulation(params: CIRParams) -> list[list[float]]:
    validate_simulation_params(params)
    if params.kappa < 0:
        raise ValueError("Kappa cannot be negative.")
    if params.theta < 0:
        raise ValueError("Theta cannot be negative.")

    dt = params.time_horizon / params.steps
    all_tracks: list[list[float]] = []

    for _ in range(params.num_tracks):
        price_paths = [params.initial_price]
        for _ in range(params.steps):
            last_price = price_paths[-1]
            noise = np.random.normal()
            drift = params.kappa * (params.theta - last_price) * dt
            diffusion = params.sigma * np.sqrt(max(last_price, 0.0)) * np.sqrt(dt) * noise
            next_price = max(last_price + drift + diffusion, 0.0)
            price_paths.append(float(next_price))
        all_tracks.append(price_paths)

    return all_tracks


def summarize_tracks(all_tracks: list[list[float]]) -> SimulationSummary:
    if not all_tracks:
        raise ValueError("Simulation returned no tracks.")

    last_prices = [track[-1] for track in all_tracks]
    average_last_price = sum(last_prices) / len(last_prices)
    return SimulationSummary(average_last_price=average_last_price, last_prices=last_prices)
