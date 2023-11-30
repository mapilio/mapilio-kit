import json

import requests
import os
import io
import typing as T

from config import MAPILIO_UPLOAD_ENDPOINT_ZIP
import types_fmt as types
import logging

LOG = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1024 * 1024 * 64


class UploadManager:
    user_access_token: str
    # This amount of data that will be loaded to memory
    entity_size: int
    session_key: str = None
    callbacks: T.List[T.Callable]

    def __init__(self, user_access_token: str, session_key: str, entity_size: int):
        if entity_size <= 0:
            raise ValueError(f"Expect positive entity size but got {entity_size}")
        self.user_access_token = user_access_token
        self.session_key = session_key
        self.entity_size = entity_size
        self.callbacks = []

    def fetch_offset(self, email) -> int:
        headers = {
            "Authorization": f"OAuth {self.user_access_token}"
        }
        resp = requests.get(
            f"{MAPILIO_UPLOAD_ENDPOINT_ZIP}?fileName={self.session_key}&email={email}",
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()

        return data["totalChunkUploaded"]

    def upload(
        self,
        user_items: types.User,
        data: T.IO[bytes],
        organization_key: str = None,
        project_key: str = None,
        offset: T.Optional[int] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        if chunk_size <= 0:
            raise ValueError("Expect positive chunk size")

        email = user_items['SettingsUsername']
        if offset is None:
            offset = self.fetch_offset(email=email)

        data.seek(offset, io.SEEK_CUR) # noqa


        while True:
            chunk = data.read(chunk_size)
            files = {'chunk': (self.session_key, chunk, "multipart/form-data")}
            headers = {
                'Connection': "keep-alive",
                "content-range": f"bytes={offset}-{self.entity_size}/{self.entity_size}",
                "X-File-Id": self.session_key,
                "Content-Length": str(self.entity_size - offset),
                "email": email,
                "project-organization-key": organization_key if organization_key else None,
                "project-key": project_key if project_key else None
            }
            try:
                resp = requests.post(
                    f"{MAPILIO_UPLOAD_ENDPOINT_ZIP}",
                    headers=headers,
                    files=files
                )
                resp.raise_for_status()
                offset += len(chunk)
                for callback in self.callbacks:
                    callback(chunk, resp)
                if not chunk:
                    if (resp.status_code != 204 and
                            resp.headers["content-type"].strip().startswith("application/json")):
                        response_dict = json.loads(resp.text)
                        return response_dict["hash"]
            except requests.exceptions.HTTPError as e:
                print(e.response.text)


    def finish(
        self, file_handle: str,
            organization_id: T.Optional[T.Union[str, int]] = None,
            project_id: T.Optional[T.Union[str, int]] = None
    ) -> int:
        headers = {
            "Authorization": f"OAuth {self.user_access_token}",
        }
        data: T.Dict[str, T.Union[str, int]] = {
            "file_handle": file_handle,
        }
        if organization_id is not None and project_id is not None:
            data["organization_id"] = organization_id
            data["project_id"] = project_id

        resp = requests.post(
            f"{MAPILIO_UPLOAD_ENDPOINT_ZIP}/finish_upload", headers=headers, json=data
        )

        resp.raise_for_status()

        data = resp.json()

        cluster_id = data.get("cluster_id")
        if cluster_id is None:
            raise RuntimeError(
                f"Upload server error: failed to create the cluster {resp.text}"
            )

        return T.cast(int, cluster_id)


# A mock class for testing only
class FakeUploadManager(UploadManager):
    upload_path = os.getenv("MAPILIO_UPLOAD_PATH", "mapilio_public_uploads")

    def upload(
        self,
        data: T.IO[bytes],
        offset: T.Optional[int] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> str:
        if offset is None:
            offset = self.fetch_offset()
        os.makedirs(FakeUploadManager.upload_path, exist_ok=True)
        filename = os.path.join(FakeUploadManager.upload_path, self.session_key)
        with open(filename, "ab") as fp:
            data.seek(offset, io.SEEK_CUR)
            while True:
                chunk = data.read(chunk_size)
                if not chunk:
                    break
                fp.write(chunk)
                for callback in self.callbacks:
                    callback(chunk, None)
        return self.session_key

    # def finish(
    #     self, file_handle: str, organization_id: T.Optional[T.Union[str, int]] = None
    # ) -> int:
    #     return 1

    def fetch_offset(self) -> int:
        try:
            with open(self.session_key, "rb") as fp:
                fp.seek(0, io.SEEK_END)
                return fp.tell()
        except FileNotFoundError:
            return 0


def _file_stats(fp: T.IO[bytes]):
    md5 = hashlib.md5()
    while True:
        buf = fp.read(DEFAULT_CHUNK_SIZE)
        if not buf:
            break
        md5.update(buf)
    fp.seek(0, os.SEEK_END)
    return md5.hexdigest(), fp.tell()


if __name__ == "__main__":
    import sys, hashlib, os
    import tqdm
    from .login import wrap_http_exception

    user_access_token = os.getenv("MAPILIO_TOOLS_USER_ACCESS_TOKEN")
    if not user_access_token:
        raise RuntimeError("MAPILIO_TOOLS_USER_ACCESS_TOKEN is required")

    path = sys.argv[1]
    with open(path, "rb") as fp:
        md5sum, entity_size = _file_stats(fp)
    session_key = sys.argv[2] if sys.argv[2:] else f"tools_test_{md5sum}"
    service = UploadManager(user_access_token, session_key, entity_size)

    print(f"session key: {session_key}")
    print(f"entity size: {entity_size}")
    print(f"initial offset: {service.fetch_offset()}")

    with open(path, "rb") as fp:
        with tqdm.tqdm(
            total=entity_size,
            initial=service.fetch_offset(),
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            service.callbacks.append(lambda chunk, _: pbar.update(len(chunk)))
            try:
                file_handle = service.upload(fp)
            except requests.HTTPError as ex:
                raise wrap_http_exception(ex)
    print(file_handle)