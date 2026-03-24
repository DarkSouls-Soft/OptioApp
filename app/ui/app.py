from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from ttkthemes import ThemedTk
except ImportError:  # pragma: no cover - optional dependency fallback
    ThemedTk = tk.Tk

try:
    from tkcalendar import DateEntry
except ImportError:  # pragma: no cover - optional dependency fallback
    class DateEntry(ttk.Entry):
        def __init__(self, master=None, date_pattern: str | None = None, **kwargs):
            super().__init__(master, **kwargs)
            self.insert(0, "Install tkcalendar for date picker support")


from app.services.csv_loader import CSVLoaderService
from app.ui.help_tab import HelpTab
from app.ui.monte_carlo_tab import MonteCarloTab
from app.ui.options_tab import OptionsTab
from app.ui.settings_tab import SettingsTab


CUSTOM_THEME_PALETTES = {
    "midnight": {
        "bg": "#1f2430",
        "panel": "#2b3245",
        "fg": "#f2f2f2",
        "accent": "#6aa9ff",
        "field_bg": "#252b3b",
        "field_fg": "#f2f2f2",
    },
    "forest": {
        "bg": "#edf4ee",
        "panel": "#d8e6db",
        "fg": "#173221",
        "accent": "#2f7d4a",
        "field_bg": "#ffffff",
        "field_fg": "#173221",
    },
    "ocean": {
        "bg": "#eaf4fb",
        "panel": "#d7eaf7",
        "fg": "#153243",
        "accent": "#1d70a2",
        "field_bg": "#ffffff",
        "field_fg": "#153243",
    },
    "sand": {
        "bg": "#f7f1e5",
        "panel": "#eadfc8",
        "fg": "#4b382a",
        "accent": "#a86b2d",
        "field_bg": "#fffaf1",
        "field_fg": "#4b382a",
    },
    "high_contrast": {
        "bg": "#000000",
        "panel": "#161616",
        "fg": "#ffffff",
        "accent": "#ffcc00",
        "field_bg": "#111111",
        "field_fg": "#ffffff",
    },
}


class OpcioApp:
    def __init__(self) -> None:
        self.root = self._create_root()
        self.root.title("Opcio")
        self.style = ttk.Style(self.root)
        self.csv_loader = CSVLoaderService()
        self.column_var = tk.StringVar(value="<CLOSE>")
        self.help_tab: HelpTab | None = None
        self._build_ui()
        self.change_theme("default")
        self._center_window()

    def _create_root(self):
        try:
            return ThemedTk(theme="arc")
        except TypeError:
            return ThemedTk()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill="both")
        self.notebook = notebook

        options_tab = OptionsTab(
            notebook,
            csv_loader=self.csv_loader,
            column_getter=self.get_selected_column,
            date_entry_cls=DateEntry,
        )
        notebook.add(options_tab, text="Options")

        monte_carlo_tab = MonteCarloTab(
            notebook,
            csv_loader=self.csv_loader,
            column_getter=self.get_selected_column,
            date_entry_cls=DateEntry,
        )
        notebook.add(monte_carlo_tab, text="Monte Carlo")

        self.help_tab = HelpTab(notebook)
        notebook.add(self.help_tab, text="Help")

        theme_choices = self.get_theme_choices()
        settings_tab = SettingsTab(
            notebook,
            theme_choices=theme_choices,
            theme_change_callback=self.change_theme,
            column_variable=self.column_var,
            version="beta-1.0.0",
        )
        notebook.add(settings_tab, text="Settings")

    def get_theme_choices(self) -> list[str]:
        theme_choices: list[str] = ["default"]

        try:
            root_themes = list(self.root.get_themes()) if hasattr(self.root, "get_themes") else []
        except Exception:
            root_themes = []

        ttk_themes = list(self.style.theme_names())
        all_themes = [*root_themes, *ttk_themes, *CUSTOM_THEME_PALETTES.keys()]
        for theme in all_themes:
            if theme not in theme_choices:
                theme_choices.append(theme)
        return theme_choices

    def get_selected_column(self) -> str:
        return self.column_var.get()

    def change_theme(self, theme: str) -> None:
        if theme == "default":
            self._apply_base_theme()
            return

        if theme in CUSTOM_THEME_PALETTES:
            self._apply_custom_theme(theme)
            return

        if hasattr(self.root, "set_theme"):
            try:
                self.root.set_theme(theme)
                self._apply_text_theme_for_standard_theme(theme)
                return
            except Exception:
                pass

        if theme in self.style.theme_names():
            self.style.theme_use(theme)
            self._apply_text_theme_for_standard_theme(theme)
            return

        self._apply_base_theme()

    def _apply_base_theme(self) -> None:
        fallback = "arc" if "arc" in self.get_theme_choices() and hasattr(self.root, "set_theme") else None
        if fallback is not None:
            try:
                self.root.set_theme(fallback)
            except Exception:
                pass
        elif "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.root.configure(bg="#f5f5f5")
        self._style_common_widgets(
            background="#f5f5f5",
            panel="#ffffff",
            foreground="#111111",
            accent="#2d6cdf",
            field_bg="#ffffff",
            field_fg="#111111",
        )
        self._apply_help_colors(background="white", foreground="black")

    def _apply_custom_theme(self, theme_name: str) -> None:
        palette = CUSTOM_THEME_PALETTES[theme_name]
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.root.configure(bg=palette["bg"])
        self._style_common_widgets(
            background=palette["bg"],
            panel=palette["panel"],
            foreground=palette["fg"],
            accent=palette["accent"],
            field_bg=palette["field_bg"],
            field_fg=palette["field_fg"],
        )
        self._apply_help_colors(background=palette["field_bg"], foreground=palette["field_fg"])

    def _apply_text_theme_for_standard_theme(self, theme: str) -> None:
        dark_themes = {"equilux", "black", "radiance", "keramik_alt"}
        if theme in dark_themes:
            self._apply_help_colors(background="#111111", foreground="#ffffff")
            return
        self._apply_help_colors(background="white", foreground="black")

    def _style_common_widgets(
        self,
        *,
        background: str,
        panel: str,
        foreground: str,
        accent: str,
        field_bg: str,
        field_fg: str,
    ) -> None:
        self.style.configure("TFrame", background=background)
        self.style.configure("TLabel", background=background, foreground=foreground)
        self.style.configure("TButton", background=panel, foreground=foreground, padding=6)
        self.style.map(
            "TButton",
            background=[("active", accent)],
            foreground=[("active", field_fg)],
        )
        self.style.configure("TNotebook", background=background, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=panel, foreground=foreground, padding=(10, 5))
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", accent)],
            foreground=[("selected", field_fg)],
        )
        self.style.configure("TEntry", fieldbackground=field_bg, foreground=field_fg)
        self.style.configure("TCombobox", fieldbackground=field_bg, foreground=field_fg)
        self.style.configure("TMenubutton", background=panel, foreground=foreground)

    def _apply_help_colors(self, background: str, foreground: str) -> None:
        if self.help_tab is not None:
            self.help_tab.apply_text_theme(background=background, foreground=foreground)

    def _center_window(self) -> None:
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        x_coord = (screen_width - width) // 2
        y_coord = max((screen_height - height) // 2 - 150, 0)
        self.root.geometry(f"+{x_coord}+{y_coord}")

    def run(self) -> None:
        self.root.mainloop()
