"""
QuickBooks Online adapter (demo implementation).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .base import DataPayload, DataProvider, DataSourceError, registry


def _demo_payload() -> dict[str, Any]:
    sample_path = Path(__file__).resolve().parents[1] / "sample_data" / "quickbooks_demo.json"
    with sample_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@registry.register("quickbooks")
class QuickBooksProvider(DataProvider):
    required_keys = ("client_id", "client_secret", "refresh_token", "realm_id")

    def load(self) -> DataPayload:
        mode = self.config.get("mode", "demo").lower()
        if mode == "demo":
            payload = _demo_payload()
        else:
            payload = self._simulate_remote_call()

        try:
            accounts = pd.DataFrame(payload["accounts"])
            ledger = pd.DataFrame(payload["ledger"])
        except KeyError as exc:
            raise DataSourceError(f"QuickBooks payload missing key: {exc}") from exc

        return {"accounts": accounts, "ledger": ledger}

    def _simulate_remote_call(self) -> dict[str, Any]:
        """
        Placeholder for a real QuickBooks API integration.

        The skeleton raises an error unless running in demo mode,
        keeping implementers aware that the production connector
        still requires wiring.
        """
        raise DataSourceError(
            "QuickBooks connector is in demo mode only. "
            "Provide mode='demo' until API credentials are wired."
        )
