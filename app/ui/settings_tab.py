from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class SettingsTab(ttk.Frame):
    def __init__(
        self,
        master: ttk.Notebook,
        theme_choices: list[str],
        theme_change_callback,
        column_variable: tk.StringVar,
        version: str = "beta-1.0.0",
    ) -> None:
        super().__init__(master)
        self.theme_change_callback = theme_change_callback
        self.column_variable = column_variable
        self._build_ui(theme_choices, version)

    def _build_ui(self, theme_choices: list[str], version: str) -> None:
        ttk.Label(self, text="Choose a theme:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.theme_var = tk.StringVar(value=theme_choices[0] if theme_choices else "default")
        ttk.OptionMenu(
            self,
            self.theme_var,
            self.theme_var.get(),
            *theme_choices,
            command=self.theme_change_callback,
        ).grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(self, text="Parameter calculation column:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        column_combo = ttk.Combobox(
            self,
            textvariable=self.column_variable,
            values=["<CLOSE>", "<OPEN>", "<HIGH>", "<LOW>"],
            state="readonly",
        )
        column_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        column_combo.set(self.column_variable.get())

        ttk.Label(
            self,
            text="Supported file formats: .csv and .txt with a similar column structure.",
            anchor="w",
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        ttk.Label(
            self,
            text=(
                "Annualization is inferred from timestamps when possible, otherwise from <PER> or a safe fallback.\n"
                "Monte Carlo also auto-calibrates likely jump-diffusion and CIR parameters from the loaded series."
            ),
            anchor="w",
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        ttk.Label(
            self,
            text=(
                "Custom themes included: midnight, forest, ocean, sand, high_contrast.\n"
                "Built-in ttk/ttkthemes themes are also available when installed."
            ),
            anchor="w",
            justify="left",
        ).grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        ttk.Label(self, text=f"Program version: {version}", anchor="center").grid(
            row=5,
            column=0,
            sticky="w",
            padx=8,
            pady=6,
        )
        self.columnconfigure(1, weight=1)
