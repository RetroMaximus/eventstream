

"""Master key loader and per-event key derivation."""

from __future__ import annotations

import base64
import hashlib
import hmac

from config.constants import MASTER_KEY_MIN_BYTES, PER_EVENT_KEY_INFO


class Keyring:
    """Loads the master key and derives per-event keys via HKDF-like expansion.

    We use stdlib hmac + sha256 to avoid extra deps.
    The master key is stored base64 in env.
    """

    def __init__(self, master_key_b64: str) -> None:
        try:
            self._master = base64.b64decode(master_key_b64, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("EVENTSTREAM_MASTER_KEY must be base64") from exc
        if len(self._master) < MASTER_KEY_MIN_BYTES:
            raise RuntimeError(
                f"Master key must be >= {MASTER_KEY_MIN_BYTES} bytes"
            )

    @property
    def master(self) -> bytes:
        return self._master

    def derive(self, info: bytes, length: int = 32) -> bytes:
        """HKDF-Expand using HMAC-SHA256 (stdlib only)."""
        prk = hmac.new(self._master, info, hashlib.sha256).digest()
        out = b""
        counter = 1
        while len(out) < length:
            out += hmac.new(prk, info + bytes([counter]), hashlib.sha256).digest()
            counter += 1
        return out[:length]

    def event_key(self, event_id: str) -> bytes:
        info = PER_EVENT_KEY_INFO + event_id.encode("utf-8")
        return self.derive(info, length=32)
