"""
PostgreSQL adapter using SQLAlchemy connection strings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from .base import DataPayload, DataProvider, DataSourceError, registry


def _demo_dataset(name: str) -> pd.DataFrame:
    sample_path = (
        Path(__file__).resolve().parents[1] / "sample_data" / f"{name}_demo.csv"
    )
    if not sample_path.exists():
        raise DataSourceError(f"Demo dataset missing: {sample_path.name}")
    return pd.read_csv(sample_path)


def _load_sql(connection: Connection, select_config: Mapping[str, Any]) -> pd.DataFrame:
    if "sql" in select_config:
        return pd.read_sql_query(text(select_config["sql"]), connection)
    table = select_config.get("table")
    if not table:
        raise DataSourceError("Dataset config must include 'sql' or 'table'")
    schema = select_config.get("schema")
    return pd.read_sql_table(table, connection, schema=schema)


@registry.register("postgres")
class PostgresProvider(DataProvider):
    required_keys = ("connection_url", "datasets")

    def load(self) -> DataPayload:
        mode = self.config.get("mode", "demo").lower()
        if mode == "demo":
            datasets: dict[str, str] = self.config.get("demo_datasets") or {
                "finance": "finance",
                "sales": "sales",
            }
            return {name: _demo_dataset(alias) for name, alias in datasets.items()}

        connection_url = self.config["connection_url"]
        try:
            engine = create_engine(connection_url, pool_pre_ping=True)
        except Exception as exc:
            raise DataSourceError(f"Failed creating engine: {exc}") from exc

        datasets_cfg: Mapping[str, Mapping[str, Any]] = self.config["datasets"]
        payload: DataPayload = {}
        with engine.connect() as conn:
            for dataset_name, select_config in datasets_cfg.items():
                payload[dataset_name] = _load_sql(conn, select_config)
        return payload
