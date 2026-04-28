"""Sanity checks for the package version metadata."""

from __future__ import annotations

import re

from mapilio_kit.components.version import VERSION


def test_version_is_string() -> None:
    assert isinstance(VERSION, str)
    assert VERSION, "VERSION must not be empty"


def test_version_follows_semver_like_format() -> None:
    # Allow X.Y.Z and X.Y.Z<suffix>; the project has historically used both.
    assert re.match(r"^\d+\.\d+\.\d+([.\-+a-zA-Z0-9]*)$", VERSION), (
        f"Unexpected version string: {VERSION!r}"
    )
