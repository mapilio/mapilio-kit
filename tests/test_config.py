"""Credential files must preserve user supplied strings literally."""

import pytest

from mapilio_kit.components.utilities import config


@pytest.mark.parametrize("password", ["plain", "prefix%m", "prefix%s", "%(missing)s", "50%%literal"])
def test_credentials_roundtrip_without_interpolation(tmp_path, password):
    path = tmp_path / "configs" / "CLIENT_USERS"
    config.create_config(str(path))
    expected = {
        "SettingsEmail": "fixture@example.invalid",
        "SettingsUsername": "fixture-user",
        "SettingsUserPassword": password,
        "SettingsUserKey": "123",
        "user_upload_token": "synthetic-token",
    }

    config.update_config(str(path), "fixture-user", expected)

    actual = config.load_user(config.load_config(str(path)), "fixture-user")
    assert actual == expected
