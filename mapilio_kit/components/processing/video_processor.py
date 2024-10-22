import datetime
import logging
import os
import shutil
import subprocess
import typing as T
from pathlib import Path

import mapilio_kit.components.geotagging.geotagger as geotagger
import mapilio_kit.components.utilities.point as P_exe
import mapilio_kit.components.blending.video_blender as video_blender
from mapilio_kit.components.logs import image_log
from mapilio_kit.components.processing import processing
from mapilio_kit.components.metadata.exif_metadata_writer import ImageExifModifier
from mapilio_kit.components.processing.ffmpeg import get_video_info, extract_video_by_idx, extract_video_by_idx_large, sort_selected_samples
from mapilio_kit.components.utilities.utilities import get_exiftool_specific_feature, get_video_size, calculate_chunk_size, is_large_video
from mapilio_kit.components.logger import MapilioLogger

ZERO_PADDING = 6
LOG = MapilioLogger().get_logger()

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


def _within_track_time_range_buffered(points, t: float) -> bool:
    # apply 1ms buffer, which is MAPCaptureTime's precision
    start_point_time = points[0].time - 0.001
    end_point_time = points[-1].time + 0.001
    return start_point_time <= t <= end_point_time


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
        video_sample_distance=None,
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
                video_sample_distance,
                video_sample_interval,
                video_duration_ratio,
            )


def extract_frames(
        video_file: str,
        import_path: str,
        video_sample_distance=None,
        video_sample_interval: float = 2.0,
        video_duration_ratio: float = 1.0,
) -> None:
    if video_sample_distance is not None and 0 <= video_sample_distance:
        _extract_frames_distance_gap(video_file,
                                     import_path,
                                     video_sample_distance)
    else:
        _extract_frames_time_slice(video_file, import_path, video_sample_interval, video_duration_ratio)


def _sample_video_stream_by_distance(
        points: T.Sequence[P_exe.Point],
        video_track_parser: video_blender.TrackBoxParser,
        sample_distance: float,
):
    """
    Locate video frames along the track (points), then resample them by the minimal sample_distance, and return the sparse frames.
    """

    LOG.info("Extracting video samples")
    sorted_samples = list(video_track_parser.parse_samples())
    # we need sort sampels by composition time (CT) not the decoding offset (DT)
    # CT is the oder of videos streaming to audiences, as well as the order ffmpeg sampling
    sorted_samples.sort(key=lambda sample: sample.composition_time_offset)
    LOG.info("Found total %d video samples", len(sorted_samples))

    # interpolate sample points between the GPS track range (with 1ms buffer)
    LOG.info(
        "Interpolating video samples in the time range from %s to %s",
        points[0].time,
        points[-1].time,
    )
    interpolator = P_exe.Interpolator([points])
    interp_sample_points = [
        (
            frame_idx_0based,
            video_sample,
            interpolator.interpolate(video_sample.composition_time_offset),
        )
        for frame_idx_0based, video_sample in enumerate(sorted_samples)
        if _within_track_time_range_buffered(
            points, video_sample.composition_time_offset
        )
    ]
    LOG.info("Found total %d interpolated video samples", len(interp_sample_points))

    # select sample points by sample distance
    selected_interp_sample_points = list(
        P_exe.filter_points_by_distance(
            interp_sample_points,
            sample_distance,
            point_func=lambda x: x[2],
        )
    )
    LOG.info(
        "Selected %d video samples by the minimal sample distance %s",
        len(selected_interp_sample_points),
        sample_distance,
    )

    return {
        frame_idx_0based: (video_sample, interp)
        for frame_idx_0based, video_sample, interp in selected_interp_sample_points
    }


def _extract_frames_distance_gap(video_file: str,
                                 import_path: str,
                                 video_sample_distance: float, ):
    start_time, video_stream = get_video_info(video_file)
    if start_time is None:
        raise LOG.error(
            f"Unable to extract video start time from {video_file}"
        )
    if not isinstance(video_file, Path): video_file = Path(video_file)
    if not isinstance(import_path, Path): import_path = Path(import_path)
    LOG.info("Extracting video metdata")
    video_metadata = geotagger.VideoGeotagHandler.geotag_video(
        video_file
    )

    if not video_stream:
        LOG.warning("no video streams found from ffprobe")
        return

    video_stream_idx = video_stream["index"]
    moov_parser = video_blender.MovieBoxParser.parse_file(video_file)
    video_track_parser = moov_parser.parse_track_at(video_stream_idx)
    sample_points_by_frame_idx = _sample_video_stream_by_distance(
        video_metadata.points, video_track_parser, video_sample_distance
    )
    sorted_sample_indices = sorted(sample_points_by_frame_idx.keys())

    video_size = get_video_size(video_file)
    LOG.info(f"Video size is equal to -> {video_size} MB. Chunk size is being calculated.")

    is_large = is_large_video(video_size)

    if is_large:

        chunk_size = calculate_chunk_size(video_size)
        LOG.info(f"Calculated chunk size is {chunk_size}. Processing...")
        LOG.info("Note that your video is a large video so, it will take more time more to process.")
        extract_video_by_idx_large(video_file, import_path, set(sorted_sample_indices), video_stream_idx, chunk_size = chunk_size)

    else:
        extract_video_by_idx(video_file, import_path, set(sorted_sample_indices), video_stream_idx)

    frame_samples = sort_selected_samples(
        import_path, video_file, [video_stream_idx]
    )

    if len(frame_samples) != len(sorted_sample_indices):
        raise Exception(
            f"Expect {len(sorted_sample_indices)} samples but extracted {len(frame_samples)} samples"
        )
    for idx, (frame_idx_1based, sample_paths) in enumerate(frame_samples):
        assert (
                len(sample_paths) == 1
        ), "Expect 1 sample path at {frame_idx_1based} but got {sample_paths}"
        if idx + 1 != frame_idx_1based:
            raise Exception(f"Expect {sample_paths[0]} to be {idx + 1}th sample but got {frame_idx_1based}"
                            )

    for (_, sample_paths), sample_idx in zip(frame_samples, sorted_sample_indices):
        if sample_paths[0] is None:
            continue

        video_sample, interp = sample_points_by_frame_idx[sample_idx]
        assert (
                interp.time == video_sample.composition_time_offset
        ), f"interpolated time {interp.time} should match the video sample time {video_sample.composition_time_offset}"
        start_time = datetime.datetime.strptime(str(start_time), '%Y-%m-%d %H:%M:%S.%f%z')
        timestamp = start_time + datetime.timedelta(seconds=interp.time)
        exif_edit = ImageExifModifier(str(sample_paths[0]))
        exif_edit.set_date_time_original(timestamp)
        exif_edit.set_gps_datetime(timestamp)
        exif_edit.set_lat_lon(interp.lat, interp.lon)
        if interp.alt is not None:
            exif_edit.set_altitude(interp.alt)
        if interp.angle is not None:
            exif_edit.set_direction(interp.angle)
        if video_metadata.make:
            exif_edit.set_make(video_metadata.make)
        if video_metadata.model:
            exif_edit.set_model(video_metadata.model)
        exif_edit.write()

def _extract_frames_time_slice(video_file: str,
                               import_path: str,
                               video_sample_interval: float = 2.0,
                               video_duration_ratio: float = 1.0,
                               ):
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
