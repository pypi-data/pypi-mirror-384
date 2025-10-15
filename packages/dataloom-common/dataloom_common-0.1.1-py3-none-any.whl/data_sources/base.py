"""
Data source abstraction used by the tier starter dashboards.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Mapping, MutableMapping, Type

import pandas as pd


DataPayload = Dict[str, pd.DataFrame]


class DataSourceError(RuntimeError):
    """Raised when an adapter fails to load data."""


class DataProvider(ABC):
    """Base class for all data source adapters."""

    key: str
    required_keys: tuple[str, ...] = ()

    def __init__(self, config: Mapping[str, Any]):
        self.config = dict(config)
        self.validate()

    def validate(self) -> None:
        missing = [key for key in self.required_keys if key not in self.config]
        if missing:
            raise DataSourceError(
                f"{self.key} adapter missing required keys: {', '.join(missing)}"
            )

    @abstractmethod
    def load(self) -> DataPayload:
        """Fetch data for dashboards and return a mapping of dataset name to DataFrame."""


class AdapterRegistry:
    def __init__(self) -> None:
        self._items: MutableMapping[str, Type[DataProvider]] = {}

    def register(self, key: str) -> Callable[[Type[DataProvider]], Type[DataProvider]]:
        def decorator(cls: Type[DataProvider]) -> Type[DataProvider]:
            if key in self._items:
                raise ValueError(f"Adapter '{key}' already registered")
            if not issubclass(cls, DataProvider):
                raise TypeError("Adapter must subclass DataProvider")
            cls.key = key
            self._items[key] = cls
            return cls

        return decorator

    def create(self, key: str, config: Mapping[str, Any]) -> DataProvider:
        try:
            adapter_cls = self._items[key]
        except KeyError as exc:
            raise DataSourceError(f"No adapter registered for key '{key}'") from exc
        return adapter_cls(config)

    def available(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


registry = AdapterRegistry()


def get_adapter(key: str, config: Mapping[str, Any]) -> DataProvider:
    return registry.create(key, config)
