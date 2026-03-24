from __future__ import annotations

from datetime import date
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, ttk

from app.domain.simulation import (
    run_cir_simulation,
    run_gbm_simulation,
    run_jump_diffusion_simulation,
    summarize_tracks,
)
from app.domain.volatility import time_to_expiration_in_years
from app.models import CIRParams, JumpDiffusionParams, MonteCarloBaseParams, TimeSeriesMetrics
from app.services.csv_loader import CSVLoaderService


MODEL_LABELS = {
    "Geometric Brownian motion": "gbm",
    "Jumping diffusion": "jump_diffusion",
    "Diffusion according to the square root law": "cir",
}


class MonteCarloTab(ttk.Frame):
    def __init__(
        self,
        master: ttk.Notebook,
        csv_loader: CSVLoaderService,
        column_getter: Callable[[], str],
        date_entry_cls,
    ) -> None:
        super().__init__(master)
        self.csv_loader = csv_loader
        self.column_getter = column_getter
        self.date_entry_cls = date_entry_cls
        self.current_annotation = None
        self.canvas: FigureCanvasTkAgg | None = None
        self.loaded_metrics: TimeSeriesMetrics | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(15, weight=1)

        ttk.Button(self, text="Select time series", command=self._load_time_series).grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )

        self.entry_s0 = self._add_entry(1, "Initial asset price (S0):")
        self.entry_mu = self._add_entry(2, "Expected return (mu):")
        self.entry_sigma = self._add_entry(3, "Model sigma:")
        self.entry_time = self._add_entry(4, "Time horizon (T):")

        ttk.Label(self, text="Select date:").grid(row=5, column=0, sticky="w")
        self.date_entry = self.date_entry_cls(self, date_pattern="dd-mm-yyyy")
        self.date_entry.grid(row=5, column=1, sticky="ew")
        if hasattr(self.date_entry, "bind"):
            self.date_entry.bind("<<DateEntrySelected>>", lambda _event: self._update_time_to_expiration())

        self.entry_steps = self._add_entry(6, "Modeling steps:", default="1000")
        self.entry_num_tracks = self._add_entry(7, "Number of tracks:", default="10")

        ttk.Label(self, text="Select a modeling method:").grid(row=8, column=0, sticky="w")
        self.model_var = tk.StringVar(value="Geometric Brownian motion")
        ttk.OptionMenu(
            self,
            self.model_var,
            "Geometric Brownian motion",
            "Geometric Brownian motion",
            "Jumping diffusion",
            "Diffusion according to the square root law",
            command=lambda _selected: self._toggle_extra_fields(),
        ).grid(row=8, column=1, sticky="ew")

        self.extra_widgets = {
            "lambda": (ttk.Label(self, text="Lambda (λ):"), ttk.Entry(self)),
            "k": (ttk.Label(self, text="k:"), ttk.Entry(self)),
            "delta": (ttk.Label(self, text="Delta (δ):"), ttk.Entry(self)),
            "kappa": (ttk.Label(self, text="Kappa (κ):"), ttk.Entry(self)),
            "theta": (ttk.Label(self, text="Theta (θ):"), ttk.Entry(self)),
        }
        self._place_extra_widgets()

        self.auto_info_label = ttk.Label(
            self,
            text="Load a time series to auto-calibrate mu/sigma and likely parameters for jump diffusion and CIR.",
            justify="left",
        )
        self.auto_info_label.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(4, 6))

        ttk.Button(self, text="Calculate", command=self.run_simulation).grid(
            row=13, column=0, columnspan=2, sticky="ew"
        )
        self.result_label = ttk.Label(self, text="", font=("Arial", 12), justify="left")
        self.result_label.grid(row=14, column=0, columnspan=2, sticky="ew")

        self._toggle_extra_fields()

    def _add_entry(self, row: int, label_text: str, default: str = "") -> ttk.Entry:
        ttk.Label(self, text=label_text).grid(row=row, column=0, sticky="w")
        entry = ttk.Entry(self)
        entry.grid(row=row, column=1, sticky="ew")
        if default:
            entry.insert(0, default)
        return entry

    def _set_entry(self, entry: ttk.Entry, value: float | str) -> None:
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    def _place_extra_widgets(self) -> None:
        positions = {
            "lambda": 9,
            "k": 10,
            "delta": 11,
            "kappa": 9,
            "theta": 10,
        }
        for name, (label, entry) in self.extra_widgets.items():
            row = positions[name]
            label.grid(row=row, column=0, sticky="w")
            entry.grid(row=row, column=1, sticky="ew")
            label.grid_remove()
            entry.grid_remove()

    def _toggle_extra_fields(self) -> None:
        for label, entry in self.extra_widgets.values():
            label.grid_remove()
            entry.grid_remove()

        selected = MODEL_LABELS[self.model_var.get()]
        if selected == "jump_diffusion":
            for key in ["lambda", "k", "delta"]:
                label, entry = self.extra_widgets[key]
                label.grid()
                entry.grid()
        elif selected == "cir":
            for key in ["kappa", "theta"]:
                label, entry = self.extra_widgets[key]
                label.grid()
                entry.grid()

        self._apply_model_defaults(update_result=False)

    def _show_error(self, message: str) -> None:
        self.result_label.config(text=message, foreground="red")

    def _show_success(self, message: str) -> None:
        self.result_label.config(text=message, foreground="green")

    def _update_time_to_expiration(self) -> None:
        try:
            if hasattr(self.date_entry, "get_date"):
                execution_date = self.date_entry.get_date()
            else:
                return
            years = time_to_expiration_in_years(execution_date, date.today())
            self._set_entry(self.entry_time, f"{years:.5f}")
        except ValueError as exc:
            self._show_error(str(exc))

    def _load_time_series(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Price series files", "*.csv *.txt"),
                ("CSV Files", "*.csv"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ]
        )
        if not file_path:
            return
        try:
            metrics = self.csv_loader.load_metrics(file_path, self.column_getter())
            self.loaded_metrics = metrics
            self._set_entry(self.entry_s0, metrics.last_price)
            self._apply_model_defaults(update_result=True)
        except ValueError as exc:
            self._show_error(str(exc))

    def _apply_model_defaults(self, update_result: bool = False) -> None:
        if self.loaded_metrics is None:
            return

        metrics = self.loaded_metrics
        model = MODEL_LABELS[self.model_var.get()]

        if model == "gbm":
            self._set_entry(self.entry_mu, f"{metrics.mu:.8f}")
            self._set_entry(self.entry_sigma, f"{metrics.sigma:.8f}")
        elif model == "jump_diffusion":
            self._set_entry(self.entry_mu, f"{metrics.jump_params.diffusive_mu:.8f}")
            self._set_entry(self.entry_sigma, f"{metrics.jump_params.diffusive_sigma:.8f}")
            self._set_entry(self.extra_widgets["lambda"][1], f"{metrics.jump_params.lambda_:.8f}")
            self._set_entry(self.extra_widgets["k"][1], f"{metrics.jump_params.k:.8f}")
            self._set_entry(self.extra_widgets["delta"][1], f"{metrics.jump_params.delta:.8f}")
        else:
            self._set_entry(self.entry_mu, "0.0")
            self._set_entry(self.entry_sigma, f"{metrics.cir_params.sigma:.8f}")
            self._set_entry(self.extra_widgets["kappa"][1], f"{metrics.cir_params.kappa:.8f}")
            self._set_entry(self.extra_widgets["theta"][1], f"{metrics.cir_params.theta:.8f}")

        if update_result:
            message = (
                f"Loaded {metrics.observations} prices. Annualization factor: {metrics.periods_per_year:.2f} "
                f"({metrics.annualization_source}).\n"
                f"GBM sigma={metrics.sigma:.6f}; Jump λ={metrics.jump_params.lambda_:.4f}, "
                f"k={metrics.jump_params.k:.6f}, δ={metrics.jump_params.delta:.6f}; "
                f"CIR κ={metrics.cir_params.kappa:.4f}, θ={metrics.cir_params.theta:.2f}."
            )
            self._show_success(message)

    def _build_base_params(self) -> MonteCarloBaseParams:
        return MonteCarloBaseParams(
            initial_price=float(self.entry_s0.get()),
            mu=float(self.entry_mu.get()),
            sigma=float(self.entry_sigma.get()),
            time_horizon=float(self.entry_time.get()),
            steps=int(self.entry_steps.get()),
            num_tracks=int(self.entry_num_tracks.get()),
        )

    def run_simulation(self) -> None:
        try:
            method = MODEL_LABELS[self.model_var.get()]
            base_params = self._build_base_params()

            if method == "gbm":
                all_tracks = run_gbm_simulation(base_params)
            elif method == "jump_diffusion":
                all_tracks = run_jump_diffusion_simulation(
                    JumpDiffusionParams(
                        **base_params.__dict__,
                        lambda_=float(self.extra_widgets["lambda"][1].get()),
                        k=float(self.extra_widgets["k"][1].get()),
                        delta=float(self.extra_widgets["delta"][1].get()),
                    )
                )
            else:
                all_tracks = run_cir_simulation(
                    CIRParams(
                        **base_params.__dict__,
                        kappa=float(self.extra_widgets["kappa"][1].get()),
                        theta=float(self.extra_widgets["theta"][1].get()),
                    )
                )

            summary = summarize_tracks(all_tracks)
            self._show_success(f"Average last price: {summary.average_last_price:.2f}")
            self._plot_simulation_results(all_tracks)
        except ValueError as exc:
            self._show_error(str(exc))

    def _plot_simulation_results(self, all_tracks: list[list[float]]) -> None:
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots()
        for track in all_tracks:
            ax.plot(track, alpha=0.5)

        average_track = np.mean(all_tracks, axis=0)
        avg_line, = ax.plot(average_track, linewidth=2, label="Average")
        ax.set_xlabel("Step")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().grid(row=15, column=0, columnspan=2, sticky="nsew")
        self.canvas.draw()
        fig.canvas.mpl_connect("motion_notify_event", lambda event: self._on_hover(event, ax, avg_line))

    def _on_hover(self, event, ax, avg_line) -> None:
        contains, _details = avg_line.contains(event)
        if contains:
            x_coord, y_coord = event.xdata, event.ydata
            if x_coord is None or y_coord is None:
                return
            if self.current_annotation is not None:
                self.current_annotation.remove()
            self.current_annotation = ax.annotate(
                f"Step: {x_coord:.0f}, Price: {y_coord:.2f}",
                xy=(x_coord, y_coord),
                textcoords="offset points",
                xytext=(10, 10),
            )
            self.canvas.draw_idle()
            return

        if self.current_annotation is not None:
            self.current_annotation.remove()
            self.current_annotation = None
            self.canvas.draw_idle()
