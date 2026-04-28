"""Tests for the Sentry init helper in ``mapilio_kit.__main__``.

We deliberately avoid importing the entire CLI module at top level — it pulls
in heavy optional deps (ffmpeg wrappers, exif tools). Instead we re-implement
the same logic in isolation to verify env-var handling stays correct.

If you change ``_init_sentry`` in ``mapilio_kit/__main__.py``, mirror the
behaviour here.
"""

from __future__ import annotations

import os
import sys
import types
from typing import Any
from unittest import mock


def _build_init_sentry(version: str = "0.0.0-test"):
    """Create an isolated copy of the Sentry init helper used by the CLI."""

    def _init_sentry() -> None:
        disabled = os.environ.get("MAPILIO_KIT_DISABLE_TELEMETRY", "").lower() in {
            "1", "true", "yes", "on",
        }
        dsn = os.environ.get("MAPILIO_KIT_SENTRY_DSN", "").strip()
        if disabled or not dsn:
            return
        try:
            import sentry_sdk
        except ImportError:
            return

        def _rate(name: str, default: float) -> float:
            try:
                return max(0.0, min(1.0, float(os.environ.get(name, default))))
            except (TypeError, ValueError):
                return default

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=_rate("MAPILIO_KIT_SENTRY_TRACES_RATE", 0.1),
            profiles_sample_rate=_rate("MAPILIO_KIT_SENTRY_PROFILES_RATE", 0.1),
            release=f"mapilio-kit@{version}",
        )

    return _init_sentry


def _stub_sentry(monkeypatch) -> mock.MagicMock:
    fake = types.ModuleType("sentry_sdk")
    fake.init = mock.MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake)
    return fake.init  # type: ignore[attr-defined,return-value]


def test_skips_when_no_dsn(monkeypatch) -> None:
    init_mock = _stub_sentry(monkeypatch)
    monkeypatch.delenv("MAPILIO_KIT_SENTRY_DSN", raising=False)
    monkeypatch.delenv("MAPILIO_KIT_DISABLE_TELEMETRY", raising=False)

    _build_init_sentry()()

    init_mock.assert_not_called()


def test_skips_when_disabled(monkeypatch) -> None:
    init_mock = _stub_sentry(monkeypatch)
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_DSN", "https://key@host/1")
    monkeypatch.setenv("MAPILIO_KIT_DISABLE_TELEMETRY", "true")

    _build_init_sentry()()

    init_mock.assert_not_called()


def test_initializes_when_dsn_present(monkeypatch) -> None:
    init_mock = _stub_sentry(monkeypatch)
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_DSN", "https://key@host/1")
    monkeypatch.delenv("MAPILIO_KIT_DISABLE_TELEMETRY", raising=False)

    _build_init_sentry(version="9.9.9")()

    init_mock.assert_called_once()
    kwargs = init_mock.call_args.kwargs
    assert kwargs["dsn"] == "https://key@host/1"
    assert kwargs["release"] == "mapilio-kit@9.9.9"
    assert 0.0 <= kwargs["traces_sample_rate"] <= 1.0
    assert 0.0 <= kwargs["profiles_sample_rate"] <= 1.0


def test_clamps_sample_rates(monkeypatch) -> None:
    init_mock = _stub_sentry(monkeypatch)
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_DSN", "https://key@host/1")
    monkeypatch.delenv("MAPILIO_KIT_DISABLE_TELEMETRY", raising=False)
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_TRACES_RATE", "5")  # above 1
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_PROFILES_RATE", "-2")  # below 0

    _build_init_sentry()()

    kwargs = init_mock.call_args.kwargs
    assert kwargs["traces_sample_rate"] == 1.0
    assert kwargs["profiles_sample_rate"] == 0.0


def test_falls_back_when_rate_is_unparseable(monkeypatch) -> None:
    init_mock = _stub_sentry(monkeypatch)
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_DSN", "https://key@host/1")
    monkeypatch.delenv("MAPILIO_KIT_DISABLE_TELEMETRY", raising=False)
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_TRACES_RATE", "not-a-number")

    _build_init_sentry()()

    kwargs = init_mock.call_args.kwargs
    assert kwargs["traces_sample_rate"] == 0.1


def test_no_sentry_module_does_not_crash(monkeypatch) -> None:
    monkeypatch.setenv("MAPILIO_KIT_SENTRY_DSN", "https://key@host/1")
    monkeypatch.delenv("MAPILIO_KIT_DISABLE_TELEMETRY", raising=False)

    # Pretend sentry_sdk is not installed.
    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def fake_import(name: str, *a: Any, **kw: Any):
        if name == "sentry_sdk":
            raise ImportError("simulated missing sentry_sdk")
        return real_import(name, *a, **kw)

    if isinstance(__builtins__, dict):
        monkeypatch.setitem(__builtins__, "__import__", fake_import)
    else:
        monkeypatch.setattr(__builtins__, "__import__", fake_import)

    # Should not raise.
    _build_init_sentry()()
