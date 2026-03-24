from __future__ import annotations

import pandas as pd

from app.domain.volatility import calculate_metrics_from_dataframe
from app.models import TimeSeriesMetrics


class CSVLoaderService:
    def load_dataframe(self, file_path: str) -> pd.DataFrame:
        read_attempts = [
            {"sep": None, "engine": "python"},
            {"sep": r"\s+", "engine": "python"},
            {"sep": ","},
            {"sep": ";"},
            {"sep": "\t"},
            {"sep": "|", "engine": "python"},
        ]

        last_error: Exception | None = None
        for read_kwargs in read_attempts:
            try:
                df = pd.read_csv(file_path, **read_kwargs)
                if len(df.columns) > 1 and not df.empty:
                    df.columns = [str(column).strip() for column in df.columns]
                    return df
            except Exception as exc:
                last_error = exc

        if last_error is not None:
            raise ValueError(f"Failed to read data file: {last_error}") from last_error
        raise ValueError("Failed to detect the file format or delimiter.")

    def load_metrics(self, file_path: str, column: str) -> TimeSeriesMetrics:
        df = self.load_dataframe(file_path)
        return calculate_metrics_from_dataframe(df, column)
