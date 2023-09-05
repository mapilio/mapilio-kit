import os
import sys
import time
import typing as T
import json
import logging


import uploader, login
import types_fmt as types

from gps_anomaly.detector import Anomaly
from utilities import photo_uuid_generate

LOG = logging.getLogger(__name__)


def read_image_descriptions(desc_path: str):
    if not os.path.isfile(desc_path):
        raise RuntimeError(
            f"Image description file {desc_path} not found. Please process it first. Exiting..."
        )

    descs: T.List[types.ImageDescriptionJSON] = []
    if desc_path == "-":
        try:
            descs = json.load(sys.stdin)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON stream from stdin")
    else:
        with open(desc_path) as fp:
            try:
                descs = json.load(fp)
            except json.JSONDecodeError:
                raise RuntimeError(f" Invalid JSON file {desc_path}")
    descs = [desc for desc in descs if ("error" not in desc) and (("heading" in desc) or ("Information" in desc))]
    return descs


def zip_images(
    import_path: str,
    zip_dir: str,
    desc_path: T.Optional[str] = None,
):
    # basic check for all
    if not import_path or not os.path.isdir(import_path):
        raise RuntimeError(f"Error, import directory {import_path} does not exist")

    if desc_path is None:
        desc_path = os.path.join(import_path, "mapilio_image_description.json")

    descs = read_image_descriptions(desc_path)

    if not descs:
        LOG.warning(f"No images found in {desc_path}. Exiting...")
        return

    uploader.zip_image_dir(import_path, descs, zip_dir)


def user_items_retriever(
    user_name: T.Optional[str] = None, organization_key: T.Optional[str] = None
) -> types.User:
    if user_name is None:
        all_user_items = login.list_all_users()
        if not all_user_items:
            raise RuntimeError("No Mapilio account found. Add one with --user_name")
        if len(all_user_items) == 1:
            user_items = all_user_items[0]
        else:
            raise RuntimeError(
                f"Found multiple Mapilio accounts. Please specify one with --user_name"
            )
    else:
        user_items = login.authenticate_user(user_name)

    # if organization_key is not None:
    #     try:
    #         resp = auth_config.fetch_organization(
    #             user_items["user_upload_token"], organization_key
    #         )
    #     except requests.HTTPError as ex:
    #         raise login.wrap_http_exception(ex) from ex
    #     org = resp.json()
    #     LOG.info(f"Uploading to organization: {json.dumps(org)}")
    #     user_items = T.cast(
    #         types.User, {**user_items, "OrganizationKey": organization_key}
    #     )
    return user_items


def upload(
    import_path: str,
    desc_path: T.Optional[str] = None,
    user_name: T.Optional[str] = None,
    organization_key: T.Optional[str] = None,
    project_key: T.Optional[str] = None,
    dry_run=False,
):
    if os.path.isfile(import_path):
        user_items = user_items_retriever(user_name, organization_key)

        uploader.zip_uploader(import_path, user_items, dry_run=dry_run)

    elif os.path.isdir(import_path):
        if desc_path is None:
            desc_path = os.path.join(import_path, "mapilio_image_description.json")

        descs = read_image_descriptions(desc_path)
        descs = photo_uuid_generate(user_email=user_name, descs=descs)
        anomaly = Anomaly()

        descs, failed_imgs, anomaly_points = anomaly.anomaly_detector(descs)

        if len(failed_imgs) > 0:

            LOG.warning(f"Some images has failed."
                        f" These images is => {failed_imgs}")
        if not descs:
            LOG.warning(f"No images found in {desc_path}. Exiting...")

            return
        user_items = user_items_retriever(user_name, organization_key)

        LOG.warning(f"If shooting was taken at a point outside the polygon,"
                    f" these points and images will be published publicly...")
        time.sleep(5)
        
        uploader.upload_image_dir_and_description(
            import_path, descs, user_items,
            dry_run=dry_run,
            organization_key=organization_key if organization_key else None,
            project_key=project_key if project_key else None)

    else:
        raise RuntimeError(f"Expect {import_path} to be either file or directory")
