from __future__ import annotations

from datetime import date
from typing import Callable

import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, ttk

from app.domain.greeks import calculate_greeks, greek_curve
from app.domain.option_pricing import black_scholes_merton, option_price_curve
from app.domain.volatility import time_to_expiration_in_years
from app.models import GraphParameter, OptionParams, TimeSeriesMetrics
from app.services.csv_loader import CSVLoaderService


GRAPH_PARAM_MAP = {
    "Price of the Underlying Asset": "underlying_price",
    "Volatility": "volatility",
}


class OptionsTab(ttk.Frame):
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
        self.option_canvas: FigureCanvasTkAgg | None = None
        self.greek_canvases: dict[str, FigureCanvasTkAgg] = {}
        self.loaded_metrics: TimeSeriesMetrics | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)

        input_frame = ttk.Frame(self)
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        input_frame.columnconfigure(1, weight=1)

        output_frame = ttk.Frame(self)
        output_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.entry_spot = self._add_entry(input_frame, 1, "Current asset price (S):")
        self.entry_strike = self._add_entry(input_frame, 2, "Option strike price (X):")
        self.entry_time = self._add_entry(input_frame, 3, "Time until option expiration (T, years):")

        ttk.Label(input_frame, text="Option exercise date:").grid(row=4, column=0, sticky="w")
        self.entry_date = self.date_entry_cls(input_frame, date_pattern="dd-mm-yyyy")
        self.entry_date.grid(row=4, column=1, sticky="ew")
        if hasattr(self.entry_date, "bind"):
            self.entry_date.bind("<<DateEntrySelected>>", lambda _event: self._update_time_to_expiration())

        self.entry_rate = self._add_entry(input_frame, 5, "Risk-free interest rate (decimal):", default="0.05")
        self.entry_sigma = self._add_entry(input_frame, 6, "Volatility (sigma):")

        ttk.Label(input_frame, text="Option type:").grid(row=7, column=0, sticky="w")
        self.option_type_var = tk.StringVar(value="call")
        ttk.OptionMenu(input_frame, self.option_type_var, "call", "call", "put").grid(row=7, column=1, sticky="ew")

        ttk.Label(input_frame, text="X-axis option for graphs:").grid(row=8, column=0, sticky="w")
        self.graph_param_var = tk.StringVar(value="Price of the Underlying Asset")
        ttk.OptionMenu(
            input_frame,
            self.graph_param_var,
            "Price of the Underlying Asset",
            "Price of the Underlying Asset",
            "Volatility",
        ).grid(row=8, column=1, sticky="ew")

        ttk.Button(input_frame, text="Select price range", command=self._load_option_metrics_from_file).grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )
        ttk.Button(input_frame, text="Calculate option price", command=self.calculate_option_price).grid(
            row=9, column=0, columnspan=2, sticky="ew"
        )
        ttk.Button(input_frame, text="Update graphs", command=self.update_graphs).grid(
            row=10, column=0, columnspan=2, sticky="ew"
        )

        self.result_label = ttk.Label(output_frame, text="", font=("Arial", 14), justify="left")
        self.result_label.grid(row=0, column=0, sticky="ew")

        self.graphs_notebook = ttk.Notebook(output_frame)
        self.graphs_notebook.grid(row=1, column=0, sticky="nsew")
        self.graphs_notebook.grid_remove()

        self.option_price_frame = ttk.Frame(self.graphs_notebook)
        self.graphs_notebook.add(self.option_price_frame, text="Option price")

        self.greek_frames: dict[str, ttk.Frame] = {}
        for greek_name in ["delta", "gamma", "theta", "vega", "rho"]:
            frame = ttk.Frame(self.graphs_notebook)
            self.greek_frames[greek_name] = frame
            self.graphs_notebook.add(frame, text=greek_name.capitalize())

    def _add_entry(self, parent: ttk.Frame, row: int, label_text: str, default: str = "") -> ttk.Entry:
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w")
        entry = ttk.Entry(parent)
        entry.grid(row=row, column=1, sticky="ew")
        if default:
            entry.insert(0, default)
        return entry

    def _set_entry(self, entry: ttk.Entry, value: float | str) -> None:
        entry.delete(0, tk.END)
        entry.insert(0, str(value))

    def _show_error(self, message: str) -> None:
        self.result_label.config(text=message, foreground="red")

    def _show_success(self, message: str) -> None:
        self.result_label.config(text=message, foreground="green")

    def _read_params(self) -> OptionParams:
        return OptionParams(
            spot=float(self.entry_spot.get()),
            strike=float(self.entry_strike.get()),
            time_to_expiration=float(self.entry_time.get()),
            risk_free_rate=float(self.entry_rate.get()),
            volatility=float(self.entry_sigma.get()),
            option_type=self.option_type_var.get(),
        )

    def _selected_graph_parameter(self) -> GraphParameter:
        return GRAPH_PARAM_MAP[self.graph_param_var.get()]

    def _update_time_to_expiration(self) -> None:
        try:
            if hasattr(self.entry_date, "get_date"):
                execution_date = self.entry_date.get_date()
            else:
                return
            years = time_to_expiration_in_years(execution_date, date.today())
            self._set_entry(self.entry_time, f"{years:.5f}")
        except ValueError as exc:
            self._show_error(str(exc))

    def _load_option_metrics_from_file(self) -> None:
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
            self._set_entry(self.entry_sigma, f"{metrics.sigma:.8f}")
            self._set_entry(self.entry_spot, f"{metrics.last_price:.8f}")
            self._show_success(
                f"Loaded S={metrics.last_price:.4f}, sigma={metrics.sigma:.6f}. "
                f"Annualization factor: {metrics.periods_per_year:.2f} ({metrics.annualization_source})."
            )
        except ValueError as exc:
            self._show_error(str(exc))

    def calculate_option_price(self) -> None:
        try:
            params = self._read_params()
            option_price = black_scholes_merton(params)
            greeks = calculate_greeks(params)
            self._show_success(
                f"Option price: {float(option_price):.4f} | "
                f"Delta: {greeks.delta:.4f} | Gamma: {greeks.gamma:.6f} | "
                f"Vega: {greeks.vega:.4f} | Theta/day: {greeks.theta:.4f} | Rho(1%): {greeks.rho:.4f}"
            )
            self._render_all_graphs(params)
            self.graphs_notebook.grid()
        except ValueError as exc:
            self._show_error(str(exc))

    def update_graphs(self) -> None:
        try:
            params = self._read_params()
            self._render_all_graphs(params)
            self.graphs_notebook.grid()
        except ValueError as exc:
            self._show_error(str(exc))

    def _render_all_graphs(self, params: OptionParams) -> None:
        self._render_option_graph(params)
        for greek_name in ["delta", "gamma", "theta", "vega", "rho"]:
            self._render_greek_graph(params, greek_name)

    def _render_option_graph(self, params: OptionParams) -> None:
        if self.option_canvas is not None:
            self.option_canvas.get_tk_widget().destroy()

        x_values, y_values, x_label = option_price_curve(params, self._selected_graph_parameter())
        fig, ax = plt.subplots()
        line, = ax.plot(x_values, y_values, label="Option price")
        ax.set_xlabel(x_label)
        ax.set_ylabel("Option price")

        if self._selected_graph_parameter() == "volatility":
            ax.axvline(x=params.volatility, linestyle="--", label=f"Volatility: {params.volatility:.5f}")
        else:
            ax.axvline(x=params.spot, linestyle="--", label=f"Spot: {params.spot:.2f}")

        ax.legend()
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=self.option_price_frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw()
        fig.canvas.mpl_connect(
            "motion_notify_event",
            lambda event: self._on_hover(event, ax, line, x_values, y_values, canvas),
        )
        self.option_canvas = canvas

    def _render_greek_graph(self, params: OptionParams, greek_name: str) -> None:
        if greek_name in self.greek_canvases:
            self.greek_canvases[greek_name].get_tk_widget().destroy()

        x_values, y_values, x_label, current_value = greek_curve(
            params,
            self._selected_graph_parameter(),
            greek_name,
        )
        frame = self.greek_frames[greek_name]

        fig, ax = plt.subplots()
        line, = ax.plot(x_values, y_values, label=f"{greek_name.capitalize()}: {current_value:.8f}")
        ax.set_xlabel(x_label)
        ax.set_ylabel(greek_name.capitalize())

        if self._selected_graph_parameter() == "volatility":
            ax.axvline(x=params.volatility, linestyle="--", label=f"Volatility: {params.volatility:.5f}")
        else:
            ax.axvline(x=params.spot, linestyle="--", label=f"Spot: {params.spot:.2f}")

        ax.legend()
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw()
        fig.canvas.mpl_connect(
            "motion_notify_event",
            lambda event: self._on_hover(event, ax, line, x_values, y_values, canvas),
        )
        self.greek_canvases[greek_name] = canvas

    def _on_hover(self, event, ax, line, x_values, y_values, canvas: FigureCanvasTkAgg) -> None:
        contains, details = line.contains(event)
        if contains:
            point_index = details["ind"][0]
            x_coord = x_values[point_index]
            y_coord = y_values[point_index]
            if self.current_annotation is not None:
                self.current_annotation.remove()
            self.current_annotation = ax.annotate(
                f"X: {x_coord:.2f}, Y: {y_coord:.5f}",
                (x_coord, y_coord),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )
            canvas.draw_idle()
            return

        if self.current_annotation is not None:
            self.current_annotation.remove()
            self.current_annotation = None
            canvas.draw_idle()
