import datetime
import os
import shutil
import subprocess
import typing as T
import logging

from mapilio_kit.components import image_log
from mapilio_kit.components import processing
from mapilio_kit.components.exif_metadata_writer import ImageExifModifier
from mapilio_kit.components.utilities import get_exiftool_specific_feature

ZERO_PADDING = 6
LOG = logging.getLogger(__name__)


def timestamp_from_filename(
    video_filename: str,
    filename: str,
    start_time: datetime.datetime,
    interval=2.0,
    adjustment=1.0,
) -> datetime.datetime:
    seconds = (
        (int(filename.rstrip(".jpg").replace(f"{video_filename}_", "").lstrip("0")) - 1)
        * interval
        * adjustment
    )

    return start_time + datetime.timedelta(seconds=seconds)


def timestamps_from_filename(
    video_filename: str,
    full_image_list: T.List[str],
    start_time: datetime.datetime,
    interval=2.0,
    adjustment=1.0,
) -> T.List[datetime.datetime]:
    capture_times: T.List[datetime.datetime] = []
    for image in full_image_list:
        capture_times.append(
            timestamp_from_filename(
                video_filename,
                os.path.basename(image),
                start_time,
                interval,
                adjustment,
            )
        )
    return capture_times


def video_sampler(
    video_import_path: str,
    import_path: str,
    video_sample_interval=2.0,
    video_start_time=None,
    video_duration_ratio=1.0,
    skip_subfolders=False,
    force_overwrite=False,
):
    if not os.path.exists(video_import_path):
        raise RuntimeError(f'Error, video path "{video_import_path}" does not exist')

    video_list = (
        image_log.get_video_file_list(video_import_path, skip_subfolders)
        if os.path.isdir(video_import_path)
        else [video_import_path]
    )

    for video in video_list:
        per_video_import_path = processing.video_sample_path(import_path, video)
        if os.path.isdir(per_video_import_path):
            images = image_log.get_total_file_list(per_video_import_path)
            if images:
                shutil.rmtree(per_video_import_path)
        elif os.path.isfile(per_video_import_path):
            os.remove(per_video_import_path)

        if not os.path.exists(per_video_import_path):
            os.makedirs(per_video_import_path)
            extract_frames(
                video,
                per_video_import_path,
                video_sample_interval,
                video_duration_ratio,
            )


def extract_frames(
    video_file: str,
    import_path: str,
    video_sample_interval: float = 2.0,
    video_duration_ratio: float = 1.0,
) -> None:
    video_filename, ext = os.path.splitext(os.path.basename(video_file))
    command = [
        "ffpb",
        "-i",
        video_file,
        "-vf",
        f"fps=1/{video_sample_interval}",
        # video quality level
        "-qscale:v",
        "1",
        "-nostdin",
        f"{os.path.join(import_path, video_filename)}_%0{ZERO_PADDING}d.jpg",
    ]

    LOG.info(f"Extracting frames: {' '.join(command)}")
    try:
        subprocess.call(command)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Please make sure it is installed in your PATH. "
            "See https://github.com/mapilio/mapilio_tools#video-support for instructions"
        )
    ebi = get_exiftool_specific_feature(video_file)  # ebi = exif basic information
    video_start_time = datetime.datetime.utcnow()

    insert_video_frame_timestamp_device_infomation(
        video_filename,
        import_path,
        video_start_time,
        video_sample_interval,
        video_duration_ratio,
        ebi['device_model'],
        ebi['device_make'],
        ebi['field_of_view']
    )


def insert_video_frame_timestamp_device_infomation(
    video_filename: str,
    video_sampling_path: str,
    start_time: datetime.datetime,
    sample_interval: float = 2.0,
    duration_ratio: float = 1.0,
    device_model=None,
    device_make=None,
    field_of_view=None
) -> None:
    frame_list = image_log.get_total_file_list(video_sampling_path)

    if not frame_list:
        LOG.warning("No video frames were extracted.")
        return

    video_frame_timestamps = timestamps_from_filename(
        video_filename, frame_list, start_time, sample_interval, duration_ratio
    )

    for image, timestamp in zip(frame_list, video_frame_timestamps):
        exif_edit = ImageExifModifier(image)
        exif_edit.set_date_time_original(timestamp)
        exif_edit.set_device_information(device_make, device_model)
        exif_edit.set_fov(field_of_view)
        exif_edit.write()
