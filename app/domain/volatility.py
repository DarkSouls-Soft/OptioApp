from __future__ import annotations

from dataclasses import replace
from datetime import date
import math
import re

import numpy as np
import pandas as pd

from app.models import CIREstimate, JumpDiffusionEstimate, TimeSeriesMetrics


SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60
PER_FALLBACK_MAP = {
    "1min": 252 * 390,
    "3min": 252 * (390 / 3),
    "5min": 252 * (390 / 5),
    "10min": 252 * (390 / 10),
    "15min": 252 * (390 / 15),
    "20min": 252 * (390 / 20),
    "30min": 252 * (390 / 30),
    "45min": 252 * (390 / 45),
    "60min": 252 * (390 / 60),
    "90min": 252 * (390 / 90),
    "120min": 252 * (390 / 120),
    "240min": 252 * (390 / 240),
    "1hour": 252 * (390 / 60),
    "1day": 252,
    "3day": 252 / 3,
    "1week": 52,
    "1month": 12,
    "1year": 1,
}


def time_to_expiration_in_years(execution_date: date, current_date: date | None = None) -> float:
    current_date = current_date or date.today()
    delta_days = (execution_date - current_date).days
    if delta_days < 0:
        raise ValueError("Due date has already passed.")
    return delta_days / 365.25


def normalize_column_name(name: str) -> str:
    return re.sub(r"[<>\s]", "", str(name)).upper()


def resolve_column_name(df: pd.DataFrame, requested_column: str) -> str:
    if requested_column in df.columns:
        return requested_column

    requested_norm = normalize_column_name(requested_column)
    for column in df.columns:
        if normalize_column_name(column) == requested_norm:
            return column

    raise ValueError(f"Column '{requested_column}' not found in data file.")


def _parse_datetime_series(df: pd.DataFrame) -> pd.Series | None:
    normalized_map = {normalize_column_name(column): column for column in df.columns}
    date_column = normalized_map.get("DATE")
    time_column = normalized_map.get("TIME")

    if date_column is None:
        return None

    date_values = df[date_column].astype(str).str.strip()
    if time_column is None:
        time_values = pd.Series(["000000"] * len(df), index=df.index)
    else:
        time_values = df[time_column].astype(str).str.strip().replace({"": "000000", "nan": "000000"})

    date_digits = date_values.str.replace(r"\D", "", regex=True)
    time_digits = time_values.str.replace(r"\D", "", regex=True)

    parsed = pd.to_datetime(
        date_digits.str.zfill(8) + time_digits.str.zfill(6),
        format="%Y%m%d%H%M%S",
        errors="coerce",
    )
    if parsed.notna().sum() >= 2:
        return parsed

    combined = date_values + " " + time_values
    parsed = pd.to_datetime(combined, errors="coerce", dayfirst=True)
    if parsed.notna().sum() >= 2:
        return parsed
    return None


def infer_periods_per_year(df: pd.DataFrame) -> tuple[float, str]:
    normalized_map = {normalize_column_name(column): column for column in df.columns}
    per_column = normalized_map.get("PER")
    per_value: str | None = None
    if per_column is not None:
        per_values = df[per_column].dropna().astype(str).str.strip().str.lower()
        if not per_values.empty:
            per_value = per_values.iloc[0]
            if per_value in PER_FALLBACK_MAP and any(
                per_value.endswith(suffix) for suffix in ("day", "week", "month", "year")
            ):
                return float(PER_FALLBACK_MAP[per_value]), f"fallback_from_PER={per_value}"

    parsed_datetimes = _parse_datetime_series(df)
    if parsed_datetimes is not None:
        timestamps = parsed_datetimes.dropna().sort_values()
        if len(timestamps) >= 3:
            span_seconds = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds()
            if span_seconds > 0:
                periods_per_year = (len(timestamps) - 1) * SECONDS_PER_YEAR / span_seconds
                if periods_per_year > 0:
                    return float(periods_per_year), "inferred_from_datetime_span"

    if per_value is not None and per_value in PER_FALLBACK_MAP:
        return float(PER_FALLBACK_MAP[per_value]), f"fallback_from_PER={per_value}"

    return 252.0, "default_252"


def _safe_sample_std(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    return float(np.std(values, ddof=1))


def estimate_jump_diffusion_params(log_returns: np.ndarray, periods_per_year: float) -> JumpDiffusionEstimate:
    if len(log_returns) == 0:
        return JumpDiffusionEstimate(
            lambda_=0.0,
            k=0.0,
            delta=0.0,
            diffusive_mu=0.0,
            diffusive_sigma=0.0,
            jump_count=0,
            threshold=0.0,
        )

    center = float(np.median(log_returns))
    mad = float(np.median(np.abs(log_returns - center)))
    robust_sigma = 1.4826 * mad
    if robust_sigma <= 0:
        robust_sigma = _safe_sample_std(log_returns)

    threshold = 4.0 * robust_sigma
    if threshold <= 0:
        jump_mask = np.zeros(len(log_returns), dtype=bool)
    else:
        jump_mask = np.abs(log_returns - center) > threshold

    jump_returns = log_returns[jump_mask]
    diffusive_returns = log_returns[~jump_mask]

    if len(diffusive_returns) < 2:
        diffusive_returns = log_returns
        jump_returns = np.array([], dtype=float)
        jump_mask = np.zeros(len(log_returns), dtype=bool)

    years_observed = max(len(log_returns) / periods_per_year, 1e-9)
    jump_count = int(jump_mask.sum())
    lambda_ = float(jump_count / years_observed)
    k = float(jump_returns.mean()) if len(jump_returns) else 0.0
    if len(jump_returns) >= 2:
        delta = _safe_sample_std(jump_returns)
    elif len(jump_returns) == 1:
        delta = max(abs(float(jump_returns[0])), robust_sigma)
    else:
        delta = 0.0

    diffusive_mu = float(diffusive_returns.mean() * periods_per_year)
    diffusive_sigma = float(_safe_sample_std(diffusive_returns) * np.sqrt(periods_per_year))

    return JumpDiffusionEstimate(
        lambda_=lambda_,
        k=k,
        delta=delta,
        diffusive_mu=diffusive_mu,
        diffusive_sigma=diffusive_sigma,
        jump_count=jump_count,
        threshold=float(threshold),
    )


def estimate_cir_params(price_series: np.ndarray, periods_per_year: float) -> CIREstimate:
    prices = np.asarray(price_series, dtype=float)
    if len(prices) < 3:
        return CIREstimate(kappa=1.0, theta=float(prices[-1]), sigma=0.1, method="fallback_short_series")

    dt = 1.0 / periods_per_year
    x_t = prices[:-1]
    x_next = prices[1:]

    if np.any(x_t <= 0):
        x_t = np.maximum(x_t, 1e-9)

    design = np.column_stack([np.ones(len(x_t)), x_t])
    try:
        coeffs, *_ = np.linalg.lstsq(design, x_next, rcond=None)
        a, b = float(coeffs[0]), float(coeffs[1])
    except np.linalg.LinAlgError:
        a, b = 0.0, 0.0

    if not (0 < b < 1):
        theta = float(np.median(prices))
        diff_prices = np.diff(prices)
        sigma = float(np.std(diff_prices, ddof=1) / math.sqrt(max(np.mean(x_t) * dt, 1e-9))) if len(diff_prices) > 1 else 0.1
        return CIREstimate(
            kappa=1.0,
            theta=max(theta, 1e-9),
            sigma=max(sigma, 1e-9),
            method="fallback_non_mean_reverting",
        )

    kappa = max(-math.log(b) / dt, 1e-9)
    theta = max(a / (1 - b), 1e-9)
    residuals = x_next - (a + b * x_t)
    denom = np.sqrt(np.maximum(x_t * dt, 1e-12))
    sigma = _safe_sample_std(residuals / denom)
    sigma = max(sigma, 1e-9)

    return CIREstimate(kappa=kappa, theta=theta, sigma=sigma, method="ols_discretization")


def calculate_metrics_from_dataframe(df: pd.DataFrame, column: str) -> TimeSeriesMetrics:
    resolved_column = resolve_column_name(df, column)
    series = pd.to_numeric(df[resolved_column], errors="coerce").dropna()
    if len(series) < 3:
        raise ValueError("The selected column must contain at least three numeric values.")
    if (series <= 0).any():
        raise ValueError("The selected column must contain only positive prices.")

    log_returns = np.log(series / series.shift(1)).dropna().to_numpy(dtype=float)
    periods_per_year, annualization_source = infer_periods_per_year(df)

    mu = float(log_returns.mean() * periods_per_year)
    sigma = float(_safe_sample_std(log_returns) * np.sqrt(periods_per_year))
    last_price = float(series.iloc[-1])

    jump_params = estimate_jump_diffusion_params(log_returns, periods_per_year)
    cir_params = estimate_cir_params(series.to_numpy(dtype=float), periods_per_year)

    return TimeSeriesMetrics(
        mu=mu,
        sigma=sigma,
        last_price=last_price,
        periods_per_year=float(periods_per_year),
        annualization_source=annualization_source,
        observations=int(len(series)),
        jump_params=jump_params,
        cir_params=cir_params,
    )
