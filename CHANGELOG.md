# Changelog

All notable changes to this project are documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.9.3] - 2026-03-24

### Added
- Modular project structure with `domain`, `services`, `ui`, and `models`.
- Support for both `.csv` and `.txt` price series files.
- Separate Help tab with built-in documentation.
- Multiple GUI themes.
- NixOS startup workflow documentation.

### Changed
- Reworked volatility and return estimation logic.
- Improved annualization handling for different timeframes.
- Corrected interpretation of Greeks scaling, including `rho`.
- Improved Monte Carlo parameter initialization for GBM, Jump Diffusion, and CIR-like process.
- Refactored GUI logic away from a single monolithic script.

### Fixed
- Incorrect handling of array inputs during validation for graph generation.
- Several GUI coupling issues between business logic and interface updates.
- Improved file parsing behavior for multiple delimiter styles.

## [0.9.0-beta] - Initial academic version, 2024-06-20

### Added
- Tkinter desktop interface.
- Black-Scholes-Merton option pricing.
- Greeks calculation.
- Monte Carlo simulation tab.
- Historical volatility estimation from imported price series.
