from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk


HELP_TEXT = """Opcio helps estimate option prices and simulate possible price paths.

Supported data files
- .csv and .txt files are supported.
- Expected structure: <TICKER>,<PER>,<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>
  or a shortened version with <CLOSE>.
- The key price column is usually <CLOSE>, but you can switch the working column in Settings.

How volatility and time-series parameters are calculated
- The program calculates log returns from the selected price column.
- Annualization is no longer hard-coded to 252 for every file.
- If DATE and TIME are available, the program infers observations per year from the timestamp span.
- If timestamps cannot be parsed, it falls back to the <PER> field or to a safe default.
- This matters because intraday files should not be annualized the same way as daily files.

Options tab
- Uses the Black-Scholes-Merton model.
- T is calculated from the selected expiration date using an ACT/365.25 basis.
- Vega and Rho are reported as sensitivity to a 1% change in volatility / rates.
- After loading a time series, the current price and historical volatility are filled automatically.

Monte Carlo tab
Three models are available:
1) Geometric Brownian Motion (GBM)
2) Jump diffusion
3) Diffusion according to the square root law (CIR-style mean reversion)

Automatic calibration in Monte Carlo
- GBM: fills mu and sigma from the loaded time series.
- Jump diffusion: detects likely jump observations with a robust threshold, then estimates:
  lambda = jump intensity,
  k = average jump size,
  delta = jump-size dispersion,
  plus diffusive mu and sigma from non-jump returns.
- CIR: estimates likely kappa, theta and sigma from a discrete mean-reversion fit.
  This is a practical approximation, not a perfect market calibration.

Important caveats
- Historical volatility is not implied volatility.
- CIR is a demo mean-reverting model and is usually more natural for rates, variance or strongly mean-reverting prices.
- Jump and CIR defaults are estimates, not universal truths handed down by the gods of stochastic calculus.

About the author
Markov Gleb

Program version: beta-1.0.0
"""


class HelpTab(ttk.Frame):
    def __init__(self, master: ttk.Notebook, help_text: str = HELP_TEXT) -> None:
        super().__init__(master)
        self.text_widget = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.text_widget.pack(expand=True, fill="both")
        self.text_widget.insert(tk.INSERT, help_text)
        self.text_widget.configure(state="disabled")

    def apply_text_theme(self, background: str, foreground: str, insertbackground: str | None = None) -> None:
        self.text_widget.configure(
            bg=background,
            fg=foreground,
            insertbackground=insertbackground or foreground,
        )
