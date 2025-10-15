"""
Centralised logging helpers shared by the tier starter repositories.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter with ISO timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "env": os.getenv("ENV", "dev"),
            "service": os.getenv("SERVICE_NAME", "unknown"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class BetterStackHandler(logging.Handler):
    """Minimal HTTPS shipper to Better Stack Logs."""

    def __init__(self, token: str):
        super().__init__()

        host = os.getenv("LOGTAIL_URL")
        if not host:
            region = (
                os.getenv("LOGTAIL_REGION") or os.getenv("BETTERSTACK_REGION") or "us"
            ).lower()
            host = (
                "https://in.logs.betterstack.com"
                if not region.startswith("eu")
                else "https://in.eu.logs.betterstack.com"
            )

        self.url = host.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            data = self.format(record).encode("utf-8")
            req = urllib.request.Request(
                self.url, data=data, headers=self.headers, method="POST"
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            # Never break the app because logging failed.
            pass


def _parse_level(level: str | int | None) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        try:
            return int(level)
        except ValueError:
            return getattr(logging, level.upper(), logging.INFO)
    env_value = os.getenv("LOG_LEVEL", "INFO")
    try:
        return int(env_value)
    except ValueError:
        return getattr(logging, env_value.upper(), logging.INFO)


def setup_logging(level: str | int | None = None, json_logs: bool | None = None) -> logging.Logger:
    """
    Idempotent logging setup reused by all tier starters.

    Parameters
    ----------
    level:
        Optional override for the log level. Accepts names or numeric values.
    json_logs:
        Force JSON log output. Defaults to True for production-like environments.
    """

    target_level = _parse_level(level)
    root = logging.getLogger()

    if json_logs is None:
        env = os.getenv("ENV", "dev").lower()
        json_logs = env not in {"dev", "local"}

    if not root.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        if json_logs:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
        root.addHandler(handler)

        token = os.getenv("LOGTAIL_TOKEN") or os.getenv("BETTERSTACK_TOKEN")
        if token:
            remote = BetterStackHandler(token)
            remote.setFormatter(JsonFormatter())
            root.addHandler(remote)

    root.setLevel(target_level)
    return root
