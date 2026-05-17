"""Regression tests for ``mapilio_kit.components.utilities.info.get_latest_version``.

Covers the IndexError bug (GitHub issue #209) caused by a hard-coded quote
delimiter that broke when version.py switched quote styles.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mapilio_kit.components.utilities.info import get_latest_version


def _mock_response(text: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


@pytest.mark.parametrize(
    "version_py_content, expected",
    [
        ('VERSION = "3.0.6"', "3.0.6"),
        ("VERSION = '3.0.5'", "3.0.5"),
        ('VERSION = "3.1.0-beta"', "3.1.0-beta"),
    ],
)
def test_get_latest_version_parses_both_quote_styles(
    version_py_content: str, expected: str
) -> None:
    with patch(
        "mapilio_kit.components.utilities.info.requests.get",
        return_value=_mock_response(version_py_content),
    ):
        assert get_latest_version() == expected


def test_get_latest_version_returns_none_on_http_error() -> None:
    with patch(
        "mapilio_kit.components.utilities.info.requests.get",
        return_value=_mock_response("", status_code=404),
    ):
        assert get_latest_version() is None


def test_get_latest_version_returns_none_when_no_version_line() -> None:
    with patch(
        "mapilio_kit.components.utilities.info.requests.get",
        return_value=_mock_response("# no version here\n"),
    ):
        assert get_latest_version() is None
