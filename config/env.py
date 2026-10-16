
"""Environment loader. Wraps python-dotenv and exposes typed getters."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class Env:
    """Thin wrapper around environment variables with type coercion."""

    def __init__(self, env_file: Path | None = None) -> None:
        self._env_file = env_file or Path(".env")
        if self._env_file.exists():
            load_dotenv(self._env_file, override=False)

    def str(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)

    def required(self, key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise RuntimeError(f"Missing required env var: {key}")
        return value

    def int(self, key: str, default: int = 0) -> int:
        raw = os.environ.get(key)
        return int(raw) if raw is not None else default

    def bool(self, key: str, default: bool = False) -> bool:
        raw = os.environ.get(key)
        if raw is None:
            return default
        return raw.strip().lower() in ("1", "true", "yes", "on")

    def path(self, key: str, default: str) -> Path:
        return Path(os.environ.get(key, default)).expanduser().resolve()

    def any(self, key: str, default: Any = None) -> Any:
        return os.environ.get(key, default)

