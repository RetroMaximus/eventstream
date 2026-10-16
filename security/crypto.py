
"""AES-GCM field encryption. Stdlib + cryptography only."""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config.constants import AES_GCM_NONCE_BYTES


class CryptoBox:
    """Encrypts/decrypts strings, bytes, and JSON-serializable objects.

    Format for strings: base64(nonce || ciphertext || tag)
    """

    def __init__(self, key: bytes) -> None:
        if len(key) not in (16, 24, 32):
            raise ValueError("AES-GCM key must be 16, 24, or 32 bytes")
        self._aes = AESGCM(key)

    def encrypt_bytes(self, plaintext: bytes, aad: bytes | None = None) -> bytes:
        nonce = os.urandom(AES_GCM_NONCE_BYTES)
        ct = self._aes.encrypt(nonce, plaintext, aad)
        return nonce + ct

    def decrypt_bytes(self, blob: bytes, aad: bytes | None = None) -> bytes:
        nonce, ct = blob[:AES_GCM_NONCE_BYTES], blob[AES_GCM_NONCE_BYTES:]
        return self._aes.decrypt(nonce, ct, aad)

    def encrypt_str(self, plaintext: str, aad: bytes | None = None) -> str:
        return base64.b64encode(
            self.encrypt_bytes(plaintext.encode("utf-8"), aad)
        ).decode("ascii")

    def decrypt_str(self, token: str, aad: bytes | None = None) -> str:
        return self.decrypt_bytes(
            base64.b64decode(token.encode("ascii")), aad
        ).decode("utf-8")

    def encrypt_json(self, obj: Any, aad: bytes | None = None) -> str:
        raw = json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self.encrypt_str(raw.decode("utf-8"), aad)

    def decrypt_json(self, token: str, aad: bytes | None = None) -> Any:
        return json.loads(self.decrypt_str(token, aad))

