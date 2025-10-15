"""
Generic warehouse adapter for custom SQL / BI-ready schemas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd
from sqlalchemy import create_engine, text

from .base import DataPayload, DataProvider, DataSourceError, registry


def _demo_frame(alias: str) -> pd.DataFrame:
    sample = Path(__file__).resolve().parents[1] / "sample_data" / f"{alias}_demo.csv"
    if not sample.exists():
        raise DataSourceError(f"Generic warehouse demo dataset missing: {sample.name}")
    return pd.read_csv(sample)


@registry.register("warehouse_generic")
class WarehouseGenericProvider(DataProvider):
    required_keys = ("datasets",)

    def load(self) -> DataPayload:
        mode = self.config.get("mode", "demo").lower()
        if mode == "demo":
            demo_map = self.config.get("demo_datasets") or {
                "overview": "overview",
            }
            return {name: _demo_frame(alias) for name, alias in demo_map.items()}

        connection_url = self.config.get("connection_url")
        if not connection_url:
            raise DataSourceError("Provide connection_url for non-demo warehouse mode")

        try:
            engine = create_engine(connection_url, pool_pre_ping=True)
        except Exception as exc:
            raise DataSourceError(f"Failed creating warehouse engine: {exc}") from exc

        datasets_cfg: Mapping[str, Mapping[str, Any]] = self.config["datasets"]
        payload: DataPayload = {}
        with engine.connect() as conn:
            for dataset_name, select_cfg in datasets_cfg.items():
                sql_stmt = select_cfg.get("sql")
                if not sql_stmt:
                    raise DataSourceError(
                        f"Dataset '{dataset_name}' requires an 'sql' statement"
                    )
                payload[dataset_name] = pd.read_sql_query(text(sql_stmt), conn)
        return payload
