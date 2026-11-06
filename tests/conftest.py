"""Shared pytest configuration.

We deliberately stub out optional native/heavy dependencies so unit tests can
run on a vanilla CI runner without installing the full pipeline. Tests that
need the real implementations should mark themselves with
``@pytest.mark.integration`` and be skipped by default.
"""

from __future__ import annotations

import os
import sys
import types

import pytest

# Disable telemetry during tests no matter what is in the environment.
os.environ.setdefault("MAPILIO_KIT_DISABLE_TELEMETRY", "1")
os.environ.pop("MAPILIO_KIT_SENTRY_DSN", None)


def _install_stub(name: str, attrs: dict | None = None) -> None:
    """Insert a placeholder module into ``sys.modules`` if it's missing."""
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    for key, value in (attrs or {}).items():
        setattr(module, key, value)
    sys.modules[name] = module


# ``calculation`` is an in-house package not always installable in CI.
# Upload retry tests import the EXIF writer too, but never convert coordinates.
_install_stub("calculation")
_install_stub(
    "calculation.util",
    {"calculate_vfov": lambda fov, w, h: round(float(fov) * float(h) / max(float(w), 1.0), 2)},
)


def _unexpected_coordinate_conversion(*args, **kwargs):
    raise AssertionError("Upload retry tests must not perform EXIF coordinate conversion")


_install_stub("calculation.geospatial_utils", {"decimal_to_dms": _unexpected_coordinate_conversion})


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless explicitly opted in."""
    run_integration = config.getoption("--run-integration", default=False)
    if run_integration:
        return
    skip_marker = pytest.mark.skip(reason="needs --run-integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked as integration (require external tools).",
    )
