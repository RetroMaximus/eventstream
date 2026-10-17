"""Unit tests for password hashing."""

from auth.passwords import PasswordHasherService


def test_hash_and_verify_roundtrip():
    svc = PasswordHasherService()
    h = svc.hash("correct horse battery staple")
    assert svc.verify("correct horse battery staple", h)
    assert not svc.verify("wrong", h)


def test_hash_is_unique_per_call():
    svc = PasswordHasherService()
    h1 = svc.hash("same password")
    h2 = svc.hash("same password")
    assert h1 != h2
    assert svc.verify("same password", h1)
    assert svc.verify("same password", h2)


def test_empty_password_rejected():
    svc = PasswordHasherService()
    try:
        svc.hash("")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_verify_with_garbage_hash():
    svc = PasswordHasherService()
    assert not svc.verify("anything", "not-a-hash")
    assert not svc.verify("anything", "")