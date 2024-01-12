import typing as T
import json
import logging
import os
import uuid

from tqdm import tqdm

import image_log, processing, error
import types_fmt as types

from colorama import init, Fore
init(autoreset=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter()
ch.setFormatter(formatter)
logger.addHandler(ch)



def get_final_mapilio_image_description(
    image: str,
) -> T.Optional[T.Tuple[types.Status, T.Mapping]]:
    ret = image_log.read_process_data_from_memory(image, "geotag_process")
    if ret is None:
        return None

    status, geotag_desc = ret
    if status != "success":
        return status, geotag_desc

    ret = image_log.read_process_data_from_memory(image, "sequence_process")
    if ret is None:
        return None

    status, sequence_desc = ret
    if status != "success":
        return status, sequence_desc

    description: dict = {}
    description.update(T.cast(dict, geotag_desc))
    # sequence desc overrides the image desc
    description.update(T.cast(dict, sequence_desc))

    ret = image_log.read_process_data_from_memory(image, "import_meta_data_process")
    if ret is not None:
        status, meta_desc = ret
        if status == "success":
            description.update(T.cast(dict, meta_desc))

    return status, T.cast(types.FinalImageDescription, description)


def insert_MAPJson(
    import_path,
    skip_subfolders=False,
    skip_process_errors=True,
    overwrite_all_EXIF_tags=False,
    overwrite_EXIF_time_tag=False,
    overwrite_EXIF_gps_tag=False,
    overwrite_EXIF_direction_tag=False,
    overwrite_EXIF_orientation_tag=False,
    desc_path: str = None,
):
    # basic check for all
    if not import_path or not os.path.isdir(import_path):
        raise RuntimeError(
            f"Error, import directory {import_path} does not exist, exiting..."
        )

    if desc_path is None:
        desc_path = os.path.join(import_path, "mapilio_image_description.json")

    images = image_log.get_total_file_list(import_path, skip_subfolders=skip_subfolders)

    descs: T.List[types.FinalImageDescriptionOrError] = []
    for image in tqdm(images, unit="files", desc="Processing image description"):
        ret = get_final_mapilio_image_description(image)
        if ret is None:
            continue

        status, desc = ret

        if status == "success":
            try:
                processing.overwrite_exif_tags(
                    image,
                    T.cast(types.FinalImageDescription, desc),
                    overwrite_all_EXIF_tags,
                    overwrite_EXIF_time_tag,
                    overwrite_EXIF_gps_tag,
                    overwrite_EXIF_direction_tag,
                    overwrite_EXIF_orientation_tag,
                )
            except Exception:
                logger.warning(f"Failed to overwrite EXIF", exc_info=True)

        relpath = os.path.relpath(image, import_path)
        dirname = os.path.dirname(relpath)
        basename = os.path.basename(relpath)
        if status == "success":
            descs.append(
                T.cast(types.FinalImageDescription, {**desc, "filename": basename, "path": dirname})
            )
        else:
            descs.append(
                T.cast(
                    types.FinalImageDescriptionError,
                    {"error": desc, "filename": basename, "path": dirname},
                )
            )
    processed_images = [desc for desc in descs if "error" not in desc]
    not_processed_images = T.cast(
        T.List[types.FinalImageDescriptionError],
        [desc for desc in descs if "error" in desc],
    )
    duplicated_images = [
        desc
        for desc in not_processed_images
        if desc["error"].get("type") == error.MapilioDuplicationError.__name__
    ]

    summary = {
        'Information': {
            "total_images": len(descs),
            "processed_images": len(processed_images),
            "failed_images": len(not_processed_images) - len(duplicated_images),
            "duplicated_images": len(duplicated_images),
            "id": uuid.uuid4().hex,
            "device_type": "Desktop"
        }
    }
    descs.append(
        T.cast(types.FinalImageDescription, {**summary})
    )

    if desc_path == "-":
        print(json.dumps(descs, indent=4))
    else:
        with open(desc_path, "w") as fp:
            json.dump(descs, fp, indent=4)

    logger.info(json.dumps(summary, indent=4))
    if 0 < summary['Information']["failed_images"]:
        if skip_process_errors:
            logger.warning(f"{Fore.YELLOW}Skipping %s failed images{Fore.RESET}", summary['Information']["failed_images"])
        else:
            raise RuntimeError(
                f"Failed to process {summary['Information']['failed_images']} images. "
                f"Check {desc_path} for details. Specify --skip_process_errors to skip these errors"
            )
    logger.info(f"{Fore.YELLOW}For more information, please check mapilio image description file which is located here: {desc_path}.{Fore.RESET}")