"""TOTP generation and verification. RFC 6238, SHA-1, 6 digits, 30 seconds."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time

from config.constants import (
    TOTP_BACKUP_CODE_BYTES,
    TOTP_BACKUP_CODE_COUNT,
    TOTP_DIGITS,
    TOTP_INTERVAL_SECONDS,
    TOTP_SECRET_BYTES,
)


class TOTP:
    """TOTP code generation and verification.

    Secret is base32 encoded, no padding. Compatible with Google Authenticator,
    Authy, 1Password, and Bitwarden.
    """

    def __init__(
        self,
        digits: int = TOTP_DIGITS,
        interval: int = TOTP_INTERVAL_SECONDS,
        secret_bytes: int = TOTP_SECRET_BYTES,
    ) -> None:
        self.digits = digits
        self.interval = interval
        self.secret_bytes = secret_bytes

    # ------------------------------------------------------------------
    # Secret handling
    # ------------------------------------------------------------------
    def generate_secret(self) -> str:
        raw = secrets.token_bytes(self.secret_bytes)
        return base64.b32encode(raw).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_secret(secret: str) -> bytes:
        # Restore padding to a multiple of 8.
        padded = secret.strip().upper()
        padded += "=" * (-len(padded) % 8)
        return base64.b32decode(padded)

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _hotp(self, secret_bytes: bytes, counter: int) -> str:
        msg = struct.pack(">Q", counter)
        digest = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
        return str(code % (10 ** self.digits)).zfill(self.digits)

    def now(self, secret: str) -> str:
        counter = int(time.time() // self.interval)
        return self._hotp(self._decode_secret(secret), counter)

    def at(self, secret: str, timestamp: int) -> str:
        counter = int(timestamp // self.interval)
        return self._hotp(self._decode_secret(secret), counter)

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    def verify(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify a code allowing +/- window intervals for clock skew."""
        if not secret or not code:
            return False
        code = code.strip().replace(" ", "")
        if not code.isdigit() or len(code) != self.digits:
            return False

        try:
            secret_bytes = self._decode_secret(secret)
        except Exception:  # noqa: BLE001
            return False

        counter = int(time.time() // self.interval)
        for offset in range(-window, window + 1):
            if hmac.compare_digest(
                self._hotp(secret_bytes, counter + offset), code
            ):
                return True
        return False

    # ------------------------------------------------------------------
    # Provisioning URI
    # ------------------------------------------------------------------
    def provisioning_uri(self, secret: str, account: str, issuer: str) -> str:
        from urllib.parse import quote

        label = quote(f"{issuer}:{account}")
        params = (
            f"secret={secret}"
            f"&issuer={quote(issuer)}"
            f"&algorithm=SHA1"
            f"&digits={self.digits}"
            f"&period={self.interval}"
        )
        return f"otpauth://totp/{label}?{params}"

    # ------------------------------------------------------------------
    # Backup codes
    # ------------------------------------------------------------------
    def generate_backup_codes(self, count: int = TOTP_BACKUP_CODE_COUNT) -> list[str]:
        codes: list[str] = []
        for _ in range(count):
            raw = secrets.token_bytes(TOTP_BACKUP_CODE_BYTES).hex().upper()
            formatted = "-".join(
                raw[i:i + 4] for i in range(0, len(raw), 4)
            )
            codes.append(formatted)
        return codes

    @staticmethod
    def normalize_backup_code(code: str) -> str:
        return code.strip().upper().replace("-", "").replace(" ", "")