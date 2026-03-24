# Limitations

## Educational scope

This project is an educational and portfolio application. It should not be treated as a production-ready pricing platform or a trading engine.

## Main limitations

### 1. Historical volatility only

The application uses historical volatility derived from past prices.

That means:

- it does not estimate implied volatility from market option prices;
- it may react poorly to regime changes;
- it can understate or overstate current market expectations.

### 2. Jump Diffusion calibration is heuristic

Jump parameters are not estimated through a full maximum-likelihood framework.

Current calibration is practical and interpretable, but approximate.

### 3. CIR-like process is experimental here

The square-root diffusion model is included as a demonstration of a mean-reverting non-negative process.

For many underlying assets, this is not the most natural price model.

### 4. GUI-first architecture

Although the project was refactored into a layered structure, it is still a desktop application centered around a Tkinter interface.

### 5. Not a market execution system

The application:

- does not connect to brokers,
- does not stream live market data,
- does not manage orders,
- does not perform portfolio risk aggregation.

### 6. Data quality dependence

All outputs depend on the quality and format of imported data. Incorrect timeframe labeling, broken timestamps, or invalid `CLOSE` series will affect model outputs.

## Recommended interpretation

Use this project as:

- a compact quant-finance portfolio project,
- a demonstration of pricing and simulation models,
- a structured GUI application for educational use.

Do not use it as the sole basis for real-money decisions.
