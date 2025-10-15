"""
Snowflake adapter placeholder.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .base import DataPayload, DataProvider, DataSourceError, registry


def _demo_table(name: str) -> pd.DataFrame:
    sample = Path(__file__).resolve().parents[1] / "sample_data" / f"{name}_demo.csv"
    if not sample.exists():
        raise DataSourceError(f"Snowflake demo dataset missing: {sample.name}")
    return pd.read_csv(sample)


@registry.register("snowflake")
class SnowflakeProvider(DataProvider):
    required_keys = ("account", "user", "password", "database", "schema")

    def load(self) -> DataPayload:
        mode = self.config.get("mode", "demo").lower()
        if mode != "demo":
            raise DataSourceError(
                "Snowflake connector is demo-only in this starter. "
                "Set mode='demo' or extend the adapter."
            )

        datasets = self.config.get("demo_datasets") or {
            "finance": "finance",
            "pipeline": "pipeline",
        }
        return {name: _demo_table(alias) for name, alias in datasets.items()}
