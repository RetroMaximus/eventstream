"""Unit tests for the CSRF service."""

from core.csrf import CsrfService


def test_safe_methods():
    assert CsrfService.is_safe_method("GET")
    assert CsrfService.is_safe_method("HEAD")
    assert CsrfService.is_safe_method("OPTIONS")
    assert not CsrfService.is_safe_method("POST")


def test_verify_roundtrip():
    token = "abc123"
    assert CsrfService.verify(token, token)
    assert not CsrfService.verify(token, "other")
    assert not CsrfService.verify(None, token)
    assert not CsrfService.verify(token, None)