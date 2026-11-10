"""A failed folder upload must be visible, exit non-zero and keep the metadata."""

import importlib.util
import json
import logging
from pathlib import Path

import pytest
import requests

from mapilio_kit.components.upload import upload as upload_module
from mapilio_kit.components.upload import uploader

USER = {"SettingsEmail": "fixture@example.invalid", "user_upload_token": "synthetic-token"}


@pytest.fixture
def folder(tmp_path, monkeypatch):
    desc_path = tmp_path / "mapilio_image_description.json"
    desc_path.write_text(json.dumps([{"filename": "a.jpg", "heading": 1.0}]))
    monkeypatch.setattr(upload_module, "user_items_retriever", lambda *_: USER)
    monkeypatch.setattr(upload_module, "photo_uuid_generate", lambda user_email, descs: descs)
    monkeypatch.setattr(upload_module.time, "sleep", lambda _: None)
    return tmp_path, desc_path


def _fail_upload(*_args, **_kwargs):
    raise RuntimeError("server said no")


def test_failed_upload_keeps_description_and_reports_it(folder, monkeypatch, caplog):
    path, desc_path = folder
    monkeypatch.setattr(uploader, "upload_image_dir_and_description", _fail_upload)
    # The project logger doesn't propagate, so listen on it directly.
    logger = upload_module.LOG
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.ERROR, logger=logger.name):
            result = upload_module.upload(str(path))
    finally:
        logger.removeHandler(caplog.handler)

    assert result["Success"] is False
    assert "server said no" in str(result["Error"])
    assert desc_path.exists()
    assert "server said no" in caplog.text
    assert str(desc_path) in caplog.text


def test_successful_upload_removes_description(folder, monkeypatch):
    path, desc_path = folder
    monkeypatch.setattr(uploader, "upload_image_dir_and_description", lambda *a, **k: None)

    assert upload_module.upload(str(path)) == {"Success": True}
    assert not desc_path.exists()


def test_interrupted_upload_keeps_description(folder, monkeypatch):
    path, desc_path = folder

    def interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(uploader, "upload_image_dir_and_description", interrupt)
    with pytest.raises(KeyboardInterrupt):
        upload_module.upload(str(path))
    assert desc_path.exists()


def _load_upload_command():
    # Loaded by path: importing mapilio_kit.base pulls in the stubbed pipeline packages.
    path = Path(upload_module.__file__).parents[2] / "base" / "loader.py"
    spec = importlib.util.spec_from_file_location("upload_command_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Upload()


def test_upload_command_raises_when_upload_fails(folder, monkeypatch):
    """main() turns this exception into an error message and a non-zero exit."""
    path, _ = folder
    monkeypatch.setattr(uploader, "upload_image_dir_and_description", _fail_upload)

    with pytest.raises(RuntimeError, match="server said no"):
        _load_upload_command().perform_task({"processed": True, "import_path": str(path)})


def test_rejected_description_upload_raises(tmp_path, monkeypatch):
    """A sequence whose descriptions are refused must not count as a success."""
    response = requests.Response()
    response.status_code = 500
    response._content = b"refused"
    response.url = "https://api.example.invalid/upload"

    monkeypatch.setattr(uploader.requests, "request", lambda *a, **k: response)
    monkeypatch.setattr(uploader.jsonschema, "validate", lambda **_: None)
    monkeypatch.setattr(uploader, "_validate_descs", lambda *_: None)
    monkeypatch.setattr(uploader, "_group_sequences_by_uuid", lambda _: {"seq": {}})
    monkeypatch.setattr(
        uploader, "_zip_and_upload_single_sequence", lambda *a, **k: {"seq": {"count": 1}}
    )
    monkeypatch.setattr(
        uploader.upload_desc,
        "__defaults__",
        (None, None, None, str(tmp_path)),
    )
    descs = [
        {"sequenceUuid": "seq", "heading": 1.0},
        {"Information": {"total_images": 1}},
    ]

    with pytest.raises(RuntimeError, match="1 of 1"):
        uploader.upload_image_dir_and_description(str(tmp_path), descs, USER)
