"""
Adapter for manual Excel/CSV uploads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .base import DataProvider, DataSourceError, DataPayload, registry


def _default_sample_path() -> Path:
    return Path(__file__).resolve().parents[1] / "sample_data" / "excel_demo.csv"


@registry.register("excel_manual")
class ExcelManualProvider(DataProvider):
    required_keys = ("schema",)

    def load(self) -> DataPayload:
        schema: Mapping[str, str] = self.config.get("schema", {})
        file_path = self.config.get("file_path")

        df = self._read_frame(file_path)
        renamed = df.rename(columns=schema)
        missing = [target for target in schema.values() if target not in renamed.columns]
        if missing:
            raise DataSourceError(
                f"Schema mapping resulted in missing columns: {', '.join(missing)}"
            )

        dataset_name = self.config.get("dataset_name", "transactions")
        return {dataset_name: renamed}

    def _read_frame(self, file_path: str | None) -> pd.DataFrame:
        path: Path
        if file_path:
            path = Path(file_path)
            if not path.exists():
                raise DataSourceError(f"Excel/CSV file not found at {path}")
        else:
            sample = self.config.get("sample_path")
            path = Path(sample) if sample else _default_sample_path()

        suffix = path.suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if suffix in {".csv"}:
            return pd.read_csv(path)
        raise DataSourceError(f"Unsupported file extension: {suffix}")
