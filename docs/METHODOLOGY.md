# Methodology

## 1. Option pricing

The option pricing workflow is based on the **Black-Scholes-Merton** model.

Inputs:

- current asset price `S`
- strike price `X`
- time to expiration `T`
- risk-free interest rate `r`
- volatility `sigma`
- option type (`call` or `put`)

The current implementation is suitable for educational pricing experiments and sensitivity analysis.

## 2. Greeks

The application computes:

- Delta
- Gamma
- Vega
- Theta
- Rho

The Greeks are derived from the same model assumptions as the Black-Scholes-Merton pricing formula.

## 3. Historical volatility

Volatility is estimated from the imported price series using returns derived from the `CLOSE` column.

General workflow:

1. Load the price series.
2. Compute returns.
3. Infer or approximate the annualization factor based on the file timeframe.
4. Estimate annualized volatility.

This project uses **historical volatility**, not implied volatility.

## 4. Monte Carlo simulation

The Monte Carlo tab supports three stochastic processes.

### 4.1 Geometric Brownian Motion (GBM)

Used as the baseline model for asset price simulation.

### 4.2 Jump Diffusion

Used to model occasional discontinuous jumps in price dynamics.

The current implementation includes heuristic calibration of:

- jump intensity `lambda`
- average jump size `k`
- jump dispersion `delta`

### 4.3 Square-root diffusion (CIR-like)

Included as an experimental mean-reverting non-negative process.

This model is better known from interest-rate and variance modeling, and its use for direct asset price modeling should be interpreted cautiously.

## 5. Time basis and annualization

The application attempts to reduce one of the most common mistakes in academic GUI pricing tools: applying a fixed annualization rule to all datasets regardless of timeframe.

The current logic tries to:

- use the `<PER>` field when it is available;
- infer a reasonable annualization factor when possible;
- fall back more gracefully when the timeframe cannot be determined exactly.

## 6. Practical purpose

The project is intended as a compact research-oriented desktop tool for:

- pricing experiments;
- sensitivity analysis;
- educational demonstrations of stochastic models;
- basic exploratory work with imported price series.
