import os

import pytest

from sacrifunk_loudness.mail import SMTPConfig, SMTPConfigError, _load_config


def _clear_smtp_env(monkeypatch):
    for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_FROM", "SMTP_SECURITY"):
        monkeypatch.delenv(var, raising=False)


def test_missing_smtp_host_raises(monkeypatch):
    _clear_smtp_env(monkeypatch)
    with pytest.raises(SMTPConfigError) as exc:
        _load_config()
    assert "SMTP_HOST" in str(exc.value)


def test_minimal_config_loads(monkeypatch):
    _clear_smtp_env(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "info@sacrifunk.com")
    monkeypatch.setenv("SMTP_PASS", "secret")

    cfg = _load_config()
    assert cfg.host == "smtp.example.com"
    assert cfg.port == 587  # default
    assert cfg.user == "info@sacrifunk.com"
    assert cfg.sender == "info@sacrifunk.com"  # defaults to SMTP_USER
    assert cfg.security == "starttls"


def test_explicit_from_overrides_user(monkeypatch):
    _clear_smtp_env(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "robot@example.com")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("SMTP_FROM", "Ahmed <info@sacrifunk.com>")

    cfg = _load_config()
    assert cfg.sender == "Ahmed <info@sacrifunk.com>"


def test_invalid_security_raises(monkeypatch):
    _clear_smtp_env(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "x@x.com")
    monkeypatch.setenv("SMTP_PASS", "x")
    monkeypatch.setenv("SMTP_SECURITY", "telnet")

    with pytest.raises(SMTPConfigError):
        _load_config()


def test_ssl_port_465(monkeypatch):
    _clear_smtp_env(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "x@x.com")
    monkeypatch.setenv("SMTP_PASS", "x")
    monkeypatch.setenv("SMTP_SECURITY", "ssl")
    monkeypatch.setenv("SMTP_PORT", "465")

    cfg = _load_config()
    assert cfg.security == "ssl"
    assert cfg.port == 465
