import io
import json
import uuid
from typing import Optional, Iterable, Tuple, Any
import typing as T
import os
import tempfile
import hashlib
import logging
from datetime import datetime

import time
import zipfile

import requests
from tqdm import tqdm
import jsonschema

import upload_manager,  exif_metadata_writer,interprocess_communication as ipc
import types_fmt as types
from login import wrap_http_exception
from config import MAPILIO_API_ENDPOINT_UPLOAD

from colorama import init, Fore
init(autoreset=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter()
ch.setFormatter(formatter)
logger.addHandler(ch)

MIN_CHUNK_SIZE = 1024 * 1024 * 2  # 32MB
MAX_CHUNK_SIZE = 1024 * 1024 * 16  # 64MB
MAX_UPLOAD_SIZE = 1024 * 1024 * 750  # 750MB



def _find_root_dir(file_list: Iterable[str]) -> Optional[str]:
    """
    find the common root path
    """
    dirs = set()
    for path in file_list:
        dirs.add(os.path.dirname(path))
    if len(dirs) == 0:
        return None
    elif len(dirs) == 1:
        return list(dirs)[0]
    else:
        return _find_root_dir(dirs)


def _group_sequences_by_uuid(
        image_descs: T.List[types.ImageDescriptionJSON],
) -> T.Dict[str, T.Dict[str, types.FinalImageDescription]]:
    sequences: T.Dict[str, T.Dict[str, types.FinalImageDescription]] = {}
    missing_sequence_uuid = str(uuid.uuid4())
    for desc in image_descs:
        sequence_uuid = desc.get("sequenceUuid", missing_sequence_uuid)
        sequence = sequences.setdefault(sequence_uuid, {})
        desc_without_filename = {**desc}
        del desc_without_filename["filename"]
        sequence[os.path.join(desc["path"], desc["filename"])] = T.cast(
            types.FinalImageDescription, desc_without_filename
        )
    return sequences


def _validate_descs(image_dir: str, image_descs: T.List[types.ImageDescriptionJSON]):
    image_descs = [desc for desc in image_descs if "Information" not in desc]
    for desc in image_descs:
        jsonschema.validate(instance=desc, schema=types.ImageDescriptionJSONSchema)
    for desc in image_descs:
        dirpath = os.path.join(desc["path"], desc["filename"])
        abspath = os.path.join(image_dir, dirpath)
        if not os.path.isfile(abspath):
            raise RuntimeError(f"Image path {abspath} not found")
    return image_descs

def upload_desc(
        image_desc: T.List[types.ImageDescriptionJSON],
        user_items: types.User,
        organization_key: T.Optional[str] = None,
        project_key: T.Optional[str] = None,
        seq_info: dict = None,
        backup_path: str = os.path.join(os.path.expanduser('~'), '.config', 'mapilio', 'configs'),
):
    """
    :param image_desc: description file path
    :param user_items: get user_upload_token for header bearer
    :param organization_key: will be upload organization key
    :param project_key: which organization key use project key to upload description json
    :param seq_info: information sequence data such as count and entity size, hash
    :param backup_path:
    :return: None
    """

    if not os.path.exists(os.path.join(backup_path, user_items['SettingsUsername'])):
        os.makedirs(os.path.join(backup_path, user_items['SettingsUsername']))
    export_backup_path = os.path.join(backup_path, user_items['SettingsUsername'])

    summary = list(image_desc).pop()
    image_desc = list(image_desc)[:-1]
    sequence_uuid = next(iter(seq_info)) # get first key from dict
    description_chunk = [desc for desc in image_desc if
                         desc.get("sequenceUuid") == sequence_uuid]
    summary['Information']['failed_images'] = summary['Information']['total_images'] - seq_info[sequence_uuid]['count'] # noqa
    summary['Information']['total_images'] = seq_info[sequence_uuid]['count'] # noqa
    summary['Information']['processed_images'] = seq_info[sequence_uuid]['count'] # noqa
    summary['Information']['sequence_uuid'] = sequence_uuid # noqa
    summary['Information'].update(seq_info[sequence_uuid]) # noqa
    payload = json.dumps({
        "options": {
            "parameters": {
                "organization_key": organization_key if organization_key else "",
                "project_key": project_key if project_key else "",
                "json_data": description_chunk,
                "summary": summary
            }
        }
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {user_items['user_upload_token']}"}

    current_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.now())
    try:
        resp = requests.request("POST", url=MAPILIO_API_ENDPOINT_UPLOAD, headers=headers, data=payload)
        with open(os.path.join(export_backup_path,
                               f'{current_time}_backup_request_{organization_key}_{project_key}.json'), 'w') as f:
            json.dump(payload, f)
        resp.raise_for_status()
        if not resp.status_code // 100 == 2:
            logger.warning(resp.text)
            return {"Success": False, "Error": f"Unexpected response {resp}"}
        return {"Success": True}
    except requests.exceptions.HTTPError as e:
        print(e.response.text)


def upload_image_dir_and_description(
        image_dir: str,
        descs: T.List[types.ImageDescriptionJSON],
        user_items: types.User,
        dry_run=False,
        organization_key: str = None,
        project_key: str = None
):
    jsonschema.validate(instance=user_items, schema=types.UserItemAttributes)

    image_descs = [desc for desc in descs if "heading" in desc]

    _validate_descs(image_dir, image_descs)

    sequences = _group_sequences_by_uuid(image_descs)
    response_list = []
    logger.info(f"{Fore.GREEN}Upload has been started.{Fore.RESET}")
    for sequence_idx, images in enumerate(sequences.values()):
        logger.info(f"🗺️{Fore.GREEN} Currently at: Sequence {sequence_idx + 1}, Total Number of Sequences: {len(sequences)}{Fore.RESET}")
        sequence_information = _zip_and_upload_single_sequence(
            image_dir,
            images,
            user_items,
            sequence_idx,
            len(sequences),
            organization_key,
            project_key,
            dry_run=dry_run,
        )
        response = upload_desc(
            image_desc=descs,
            user_items=user_items,
            organization_key=organization_key if organization_key else None,
            project_key=project_key if project_key else None,
            seq_info=sequence_information
        )

        response_list.append(response['Success'])

    if any(response_list):
        logger.warning(f"{Fore.GREEN}Upload has been successfully finished. {sum(response_list)} sequence(s) out of {len(response_list)} sequences were uploaded correctly. Thanks for your contributions to Mapilio 🎉!{Fore.RESET}")


def zip_image_dir(
        image_dir: str, image_descs: T.List[types.ImageDescriptionJSON], zip_dir: str
):
    image_descs=_validate_descs(image_dir, image_descs)
    sequences = _group_sequences_by_uuid(image_descs)
    os.makedirs(zip_dir, exist_ok=True)
    for sequence_uuid, sequence in sequences.items():
        # FIXME: do not use UUID as filename
        zip_filename_wip = os.path.join(
            zip_dir, f"mapilio_tools_{sequence_uuid}.{os.getpid()}.wip"
        )
        with open(zip_filename_wip, "wb") as fp:
            sequence_md5 = _zip_sequence(image_dir, sequence, fp)
        zip_filename = os.path.join(zip_dir, f"mapilio_tools_{sequence_md5}.zip")
        os.rename(zip_filename_wip, zip_filename)


class Notifier:
    def __init__(self, sequnece_info: T.Dict):
        self.uploaded_bytes = 0
        self.sequence_info = sequnece_info

    def notify_progress(self, chunk: bytes, _):
        self.uploaded_bytes += len(chunk)
        payload = {
            "chunk_size": len(chunk),
            "uploaded_bytes": self.uploaded_bytes,
            **self.sequence_info,
        }
        ipc.send_message("upload", payload)


def _zip_sequence(
        image_dir: str,
        sequences: T.Dict[str, types.FinalImageDescription],
        fp: T.IO[bytes],
        tqdm_desc: str = "Compressing",
) -> str:
    file_list = list(sequences.keys())
    first_image = list(sequences.values())[0]

    root_dir = _find_root_dir(file_list)
    if root_dir is None:
        sequence_uuid = first_image.get("sequenceUuid")
        raise RuntimeError(f"Unable to find the root dir of sequence {sequence_uuid}")

    sequence_md5 = hashlib.md5()

    file_list.sort(key=lambda path: sequences[path]["captureTime"])

    # compressing
    with zipfile.ZipFile(fp, "w", zipfile.ZIP_DEFLATED) as ziph:
        for file in tqdm(file_list, unit="files", desc=tqdm_desc):
            relpath = os.path.relpath(file, root_dir)
            abspath = os.path.join(image_dir, file)
            edit = exif_metadata_writer.ImageExifModifier(abspath)
            # edit.add_image_description(sequences[file]) # comment because changing md5sum values each run
            image_bytes = edit.serialize_image_data()
            sequence_md5.update(image_bytes)
            ziph.writestr(relpath, image_bytes)

    return sequence_md5.hexdigest()


def zip_uploader(zip_path: str, user_items: types.User, dry_run=False):
    with zipfile.ZipFile(zip_path) as ziph:
        namelist = ziph.namelist()

    if not namelist:
        raise RuntimeError(f"The zip file {zip_path} is empty")

    basename = os.path.basename(zip_path)
    with open(zip_path, "rb") as fp:
        fp.seek(0, io.SEEK_END)
        entity_size = fp.tell()

        # chunk size
        avg_image_size = int(entity_size / len(namelist))
        chunk_size = min(max(avg_image_size, MIN_CHUNK_SIZE), MAX_CHUNK_SIZE)

        notifier = Notifier(
            {
                "sequence_path": zip_path,
                "sequence_uuid": "",
                "total_bytes": entity_size,
                "sequence_idx": 0,
                "total_sequences": 1,
            }
        )

        return _upload_zipfile_fp(
            user_items,
            fp,
            entity_size,
            chunk_size,
            session_key=basename,
            tqdm_desc="Uploading",
            notifier=notifier,
            dry_run=dry_run,
        )


def is_retriable_exception(ex: Exception):
    if isinstance(ex, (requests.ConnectionError, requests.Timeout)):
        return True

    if isinstance(ex, requests.HTTPError):
        if 400 <= ex.response.status_code < 500:
            try:
                resp = ex.response.json()
            except json.JSONDecodeError:
                return False
            return resp.get("debug_info", {}).get("retriable", False)
        else:
            return True

    return False


def _upload_zipfile_fp(
        user_items: types.User,
        fp: T.IO[bytes],
        entity_size: int,
        chunk_size: int = None,
        organization_key: str = None,
        project_key: str = None,
        session_key: str = None,
        tqdm_desc: str = "Uploading",
        notifier: Optional[Notifier] = None,
        dry_run: bool = False,
) -> str:
    """
    :param fp: the file handle to a zipped sequence file. Will always upload from the beginning
    :param entity_size: the size of the whole zipped sequence file
    :param session_key: the upload session key used to identify an upload
    :return: cluster ID
    """

    if session_key is None:
        session_key = str(uuid.uuid4())

    user_access_token = user_items["user_upload_token"]
    # uploading
    if dry_run:
        upload_service: upload_manager.UploadManager = upload_manager.FakeUploadManager(
            user_access_token,
            session_key=session_key,
            entity_size=entity_size,
        )
    else:
        upload_service = upload_manager.UploadManager(
            user_access_token,
            session_key=session_key,
            entity_size=entity_size,
        )

    retries = 0

    # when it progresses, we reset retries
    def _reset_retries(_, __):
        nonlocal retries
        retries = 0

    while True:
        with tqdm(
                total=upload_service.entity_size,
                desc=tqdm_desc,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
        ) as pbar:
            fp.seek(0, io.SEEK_SET)
            update_pbar = lambda chunk, _: pbar.update(len(chunk))
            try:
                offset = upload_service.fetch_offset(email=user_items['SettingsUsername'])
                # set the initial progress
                pbar.update(offset)
                upload_service.callbacks = [
                    update_pbar,
                    _reset_retries,
                ]
                if notifier:
                    notifier.uploaded_bytes = offset
                    upload_service.callbacks.append(notifier.notify_progress)
                uploaded_hash = upload_service.upload(user_items,
                                                      fp, organization_key, project_key,
                                                      chunk_size=chunk_size, offset=offset
                                                      )
            except Exception as ex:
                if retries < 200 and is_retriable_exception(ex):
                    retries += 1
                    sleep_for = min(2 ** retries, 16)
                    logger.warning(
                        f"Error uploading, resuming in {sleep_for} seconds",
                        exc_info=True,
                    )
                    time.sleep(sleep_for)
                else:
                    if isinstance(ex, requests.HTTPError):
                        raise wrap_http_exception(ex) from ex
                    else:
                        raise ex
            else:
                break

    return uploaded_hash


def _zip_and_upload_single_sequence(
        image_dir: str,
        sequences: T.Dict[str, types.FinalImageDescription],
        user_items: types.User,
        sequence_idx: int,
        total_sequences: int,
        organization_key: str = None,
        project_key: str = None,
        dry_run=False,
) -> dict:
    def _build_desc(desc: str) -> str:
        return f"{desc} {sequence_idx + 1}/{total_sequences}"

    file_list = list(sequences.keys())
    first_image = list(sequences.values())[0]
    sequence_uuid = first_image.get("sequenceUuid")

    root_dir = _find_root_dir(file_list)
    if root_dir is None:
        raise RuntimeError(f"Unable to find the root dir of sequence {sequence_uuid}")

    sequence_info = {}
    with tempfile.NamedTemporaryFile() as fp:
        sequence_md5 = _zip_sequence(
            image_dir, sequences, fp, tqdm_desc=_build_desc("Compressing")
        )

        fp.seek(0, io.SEEK_END) # noqa
        entity_size = fp.tell()

        # chunk size
        avg_image_size = int(entity_size / len(sequences))
        chunk_size = min(max(avg_image_size, MIN_CHUNK_SIZE), MAX_CHUNK_SIZE)

        notifier = Notifier(
            {
                "sequence_path": root_dir,
                "sequence_uuid": sequence_uuid,
                "total_bytes": entity_size,
                "sequence_idx": sequence_idx,
                "total_sequences": total_sequences,
            }
        )
        uploaded_hash = _upload_zipfile_fp(
            user_items,
            fp,
            entity_size,
            chunk_size,
            organization_key,
            project_key,
            session_key=f"mapilio_tools_{sequence_md5}.zip",
            tqdm_desc=_build_desc("Uploading"),
            notifier=notifier,
            dry_run=dry_run,
        )
        sequence_info[sequence_uuid] = {
            "count": len(sequences),
            "size": entity_size / 1024 ** 2,
            "hash": uploaded_hash
        }

        return sequence_info
