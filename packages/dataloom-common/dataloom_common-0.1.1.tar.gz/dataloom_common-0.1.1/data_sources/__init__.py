"""
Adapter registry exports.
"""

from .base import DataPayload, DataProvider, DataSourceError, get_adapter, registry

# Import adapters for side effects (registration)
from . import excel as _excel  # noqa: F401
from . import quickbooks as _quickbooks  # noqa: F401
from . import postgres as _postgres  # noqa: F401
from . import snowflake as _snowflake  # noqa: F401
from . import warehouse as _warehouse  # noqa: F401

__all__ = [
    "DataPayload",
    "DataProvider",
    "DataSourceError",
    "get_adapter",
    "registry",
]
