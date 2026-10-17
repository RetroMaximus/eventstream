"""Unit tests for TOTP."""

import time

from auth.totp import TOTP


def test_secret_is_base32_and_valid():
    t = TOTP()
    s = t.generate_secret()
    assert isinstance(s, str)
    assert len(s) >= 16
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in s)


def test_code_is_six_digits():
    t = TOTP()
    s = t.generate_secret()
    code = t.now(s)
    assert len(code) == 6
    assert code.isdigit()


def test_verify_accepts_current_code():
    t = TOTP()
    s = t.generate_secret()
    code = t.now(s)
    assert t.verify(s, code)


def test_verify_rejects_wrong_code():
    t = TOTP()
    s = t.generate_secret()
    assert not t.verify(s, "000000" if t.now(s) != "000000" else "111111")


def test_verify_allows_clock_skew():
    t = TOTP()
    s = t.generate_secret()
    past = t.at(s, int(time.time()) - 30)
    assert t.verify(s, past, window=1)


def test_provisioning_uri_contains_issuer_and_account():
    t = TOTP()
    s = t.generate_secret()
    uri = t.provisioning_uri(s, "user@example.com", "eventstream")
    assert uri.startswith("otpauth://totp/")
    assert "issuer=eventstream" in uri
    assert "secret=" in uri


def test_backup_codes_are_unique_and_formatted():
    t = TOTP()
    codes = t.generate_backup_codes()
    assert len(codes) == 10
    assert len(set(codes)) == 10
    for c in codes:
        assert "-" in c


def test_normalize_backup_code():
    t = TOTP()
    assert t.normalize_backup_code("1a2b-3c4d") == "1A2B3C4D"
    assert t.normalize_backup_code(" 1A2B 3C4D ") == "1A2B3C4D"