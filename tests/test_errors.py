"""Smoke tests for the custom exception hierarchy."""

from __future__ import annotations

import pytest

from mapilio_kit.components.utilities.error import (
    MapilioDuplicationError,
    MapilioGeoTaggingError,
    MapilioUserError,
)


def test_geotagging_error_is_user_error() -> None:
    assert issubclass(MapilioGeoTaggingError, MapilioUserError)


def test_duplication_error_carries_desc() -> None:
    err = MapilioDuplicationError("duplicate", desc={"id": 1})
    assert str(err) == "duplicate"
    assert err.desc == {"id": 1}


def test_user_error_can_be_raised_and_caught() -> None:
    with pytest.raises(MapilioUserError):
        raise MapilioGeoTaggingError("boom")
