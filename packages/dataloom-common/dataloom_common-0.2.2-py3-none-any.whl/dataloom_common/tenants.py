"""
Tenant configuration helpers shared by the starter repositories.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TenantMetadata:
    slug: str
    tier: str
    adapter: str
    render_url: str | None = None
    display_name: str | None = None


@dataclass(frozen=True)
class TenantConfig:
    metadata: TenantMetadata
    adapter_config: Mapping[str, Any]
    secrets_ref: str | None = None


class TenantRegistryError(RuntimeError):
    """Raised when a tenant registry entry is invalid."""


def _default_registry_path() -> Path:
    env = os.getenv("TENANT_REGISTRY_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "sample_data" / "tenants.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise TenantRegistryError(f"Tenant registry file not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _ensure_iterable(data: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(data, dict):
        return data.values()
    if isinstance(data, list):
        return data
    raise TenantRegistryError("Tenant registry root must be a list or mapping")


def load_tenant_config(path: str | Path | None = None) -> dict[str, TenantConfig]:
    """
    Load tenant definitions from JSON.

    The shape is designed to be compatible with the auth service as well as the
    tenant bootstrap scripts. Each entry requires ``slug``, ``tier`` and
    ``adapter`` keys, plus an ``adapter_config`` object.
    """

    target_path = Path(path) if path else _default_registry_path()
    raw = _load_json(target_path)
    tenants: dict[str, TenantConfig] = {}
    for item in _ensure_iterable(raw):
        slug = item.get("slug")
        tier = item.get("tier")
        adapter = item.get("adapter")
        adapter_config = item.get("adapter_config") or {}

        if not slug or not tier or not adapter:
            raise TenantRegistryError(
                f"Tenant entry missing required fields: {item}"
            )

        metadata = TenantMetadata(
            slug=slug,
            tier=tier,
            adapter=adapter,
            render_url=item.get("render_url"),
            display_name=item.get("display_name"),
        )
        tenants[slug] = TenantConfig(
            metadata=metadata,
            adapter_config=adapter_config,
            secrets_ref=item.get("secrets_ref"),
        )
    return tenants
