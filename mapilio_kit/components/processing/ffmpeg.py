import datetime
import json
import os
import platform
import subprocess
import tempfile
import re

from mapilio_kit.components.logger import MapilioLogger

LOG = MapilioLogger().get_logger()


def get_ffprobe(path: str) -> dict:
    if not os.path.isfile(path):
        raise RuntimeError(f"No such file: {path}")

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    #LOG.info(f"Extracting video information: {' '.join(cmd)}")
    try:
        output = subprocess.check_output(cmd)
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not found. Please make sure it is installed in your PATH. "
            "See https://github.com/mapilio/mapilio_tools#video-support for instructions"
        )

    try:
        j_obj = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError(f"Error JSON decoding {output.decode('utf-8')}")

    return j_obj




def get_video_info(video_path):
    def _get_start_time(format_info):

        start_time_str = format_info.get("start_time")
        if start_time_str is None:
            LOG.error("Failed to extract start time")
            return None

        start_time = float(start_time_str)

        duration_str = format_info.get("duration")
        if duration_str is None:
            LOG.error("Failed to extract duration")
            return None

        duration = float(duration_str)

        creation_time_str = format_info.get("tags", {}).get("creation_time")
        LOG.debug("Extracted video creation time: %s", creation_time_str)
        if creation_time_str is None:
            LOG.error("Failed to extract creation time")
            return None

        try:
            creation_time = datetime.datetime.fromisoformat(creation_time_str)
        except ValueError:
            try:
                creation_time = datetime.datetime.strptime(creation_time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            except ValueError:
                LOG.error("Failed to parse creation time")
                return None

        adjusted_creation_time = creation_time - datetime.timedelta(seconds=duration)

        # Return the adjusted creation time in the desired format
        adjusted_creation_time_str = adjusted_creation_time.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        return adjusted_creation_time_str

    try:
        # Run ffprobe to get the start time, duration, and creation time with additional options
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-hide_banner',
                '-show_format',
                '-show_streams',
                '-show_entries', 'format=start_time,duration:format_tags=creation_time',
                '-of', 'json',
                video_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Parse the output
        output = result.stdout.strip()
        video_info = json.loads(output)
        start_time = _get_start_time(format_info=video_info.get("format", {}))
        video_streams = video_info.get("streams", [])
        video_streams.sort(
            key=lambda s: s.get("width", 0) * s.get("height", 0), reverse=True
        )
        return start_time, video_streams[0]

    except Exception as e:
        LOG.error(f"Error getting video info: {e}")
        return None


def extract_stream(source: str, dest: str, stream_id: int) -> None:
    if not os.path.isfile(source):
        raise RuntimeError(f"No such file: {source}")

    cmd = [
        "ffmpeg",
        "-i",
        source,
        "-y",  # overwrite - potentially dangerous
        "-nostats",
        "-loglevel",
        "0",
        "-codec",
        "copy",
        "-map",
        "0:" + str(stream_id),
        "-f",
        "rawvideo",
        dest,
    ]

    #LOG.info(f"Extracting frames: {' '.join(cmd)}")
    try:
        subprocess.check_output(cmd)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Please make sure it is installed in your PATH. "
            "See https://github.com/mapilio/mapilio_tools#video-support for instructions"
        )

def extract_video_by_idx_large(video_path,
                         sample_dir,
                         frame_indices,
                         stream_idx,
                         chunk_size,
                         FRAME_EXT=".jpg",
                         NA_STREAM_IDX="NA",
                         ):

    if not frame_indices:
        return

    sample_prefix = sample_dir.joinpath(video_path.stem)
    if stream_idx is not None:
        stream_selector = ["-map", f"0:{stream_idx}"]
        output_template = f"{sample_prefix}_{stream_idx}_%06d{FRAME_EXT}"
        stream_specifier = f"{stream_idx}"
    else:
        stream_selector = []
        output_template = f"{sample_prefix}_{NA_STREAM_IDX}_%06d{FRAME_EXT}"
        stream_specifier = "v"

    # Sort frame indices to ensure correct order
    sorted_indices = sorted(frame_indices)

    # Process frames in chunks
    for i in range(0, len(sorted_indices), chunk_size):
        chunk = sorted_indices[i:i + chunk_size]

        # Create a select filter for the current chunk
        select_expr = "+".join(f"eq(n,{idx})" for idx in chunk)

        cmd = [
            "ffpb",
            "-hide_banner",
            "-nostdin",
            "-i", str(video_path),
            *stream_selector,
            "-vf", f"select='{select_expr}',setpts=N/FRAME_RATE/TB",
            "-vsync", "0",
            "-q:v", "2",
            "-start_number", str(i + 1),
            f"{sample_prefix}_{stream_idx if stream_idx is not None else NA_STREAM_IDX}_%06d{FRAME_EXT}"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            LOG.error(f"Error extracting frames: {e}")
            LOG.error(f"ffpb stdout: {e.stdout}")
            LOG.error(f"ffpb stderr: {e.stderr}")
            raise

        LOG.info(f"Extracted chunk {i // chunk_size + 1} with {len(chunk)} frames")

    extracted_files = sorted(sample_dir.glob(f"{video_path.stem}_{stream_idx if stream_idx is not None else NA_STREAM_IDX}_*{FRAME_EXT}"))
    for index, file in enumerate(extracted_files, start=1):
        new_name = f"{sample_prefix}_{stream_idx if stream_idx is not None else NA_STREAM_IDX}_{index:06d}{FRAME_EXT}"
        file.rename(new_name)

    LOG.info(f"Extracted and renamed a total of {len(extracted_files)} frames")

def extract_video_by_idx(video_path,
                         sample_dir,
                         frame_indices,
                         stream_idx,
                         FRAME_EXT=".jpg",
                         NA_STREAM_IDX="NA"

                         ):
    if not frame_indices:
        return

    sample_prefix = sample_dir.joinpath(video_path.stem)
    if stream_idx is not None:
        stream_selector = ["-map", f"0:{stream_idx}"]
        ouput_template = f"{sample_prefix}_{stream_idx}_%06d{FRAME_EXT}"
        stream_specifier = f"{stream_idx}"
    else:
        stream_selector = []
        ouput_template = f"{sample_prefix}_{NA_STREAM_IDX}_%06d{FRAME_EXT}"
        stream_specifier = "v"

    eqs = "+".join(f"eq(n\\,{idx})" for idx in sorted(frame_indices))

    if platform.system() == "Windows":
        delete = False
    else:
        delete = True

    with tempfile.NamedTemporaryFile(mode="w+", delete=delete) as select_file:
        try:
            select_file.write(f"select={eqs}")
            select_file.flush()
            if not delete:
                select_file.close()
            cmd = ["ffpb",
                   *["-hide_banner", "-nostdin"],
                   *["-i", str(video_path)],
                   *stream_selector,
                   *[
                       *["-filter_script:v", select_file.name],
                       *["-vsync", "0"],
                       *[f"-frames:{stream_specifier}", str(len(frame_indices))],
                   ],
                   *[f"-qscale:{stream_specifier}", "2"],
                   ouput_template,
                   ]
            subprocess.check_output(cmd)
        finally:
            if not delete:
                try:
                    os.remove(select_file.name)
                except FileNotFoundError:
                    pass


def iterate_samples(
        sample_dir, video_path,
        FRAME_EXT=".jpg",
        NA_STREAM_IDX="NA",
):
    def _extract_stream_frame_idx(
            sample_basename: str,
            sample_basename_pattern,
    ):
        """
        extract stream id and frame index from sample basename
        e.g. basename GX010001_NA_000000.jpg will extract (None, 0)
        e.g. basename GX010001_1_000002.jpg will extract (1, 2)
        If returning None, it means the basename does not match the pattern
        """
        image_no_ext, ext = os.path.splitext(sample_basename)
        if ext.lower() != FRAME_EXT.lower():
            return None

        match = sample_basename_pattern.match(image_no_ext)
        if not match:
            return None

        g1 = match.group("stream_idx")
        try:
            if g1 == NA_STREAM_IDX:
                stream_idx = None
            else:
                stream_idx = int(g1)
        except ValueError:
            return None

        # convert 0-padded numbers to int
        # e.g. 000000 -> 0
        # e.g. 000001 -> 1
        g2 = match.group("frame_idx")
        g2 = g2.lstrip("0") or "0"

        try:
            frame_idx = int(g2)
        except ValueError:
            return None

        return stream_idx, frame_idx

    sample_basename_pattern = re.compile(
        rf"^{re.escape(video_path.stem)}_(?P<stream_idx>\d+|{re.escape(NA_STREAM_IDX)})_(?P<frame_idx>\d+)$"
    )
    for sample_path in sample_dir.iterdir():
        stream_frame_idx = _extract_stream_frame_idx(
            sample_path.name,
            sample_basename_pattern,
        )
        if stream_frame_idx is not None:
            stream_idx, frame_idx = stream_frame_idx
            yield (stream_idx, frame_idx, sample_path)


def sort_selected_samples(
        sample_dir, video_path, selected_stream_indices
):
    stream_samples = {}
    for stream_idx, frame_idx, sample_path in iterate_samples(sample_dir, video_path):
        stream_samples.setdefault(frame_idx, []).append((stream_idx, sample_path))

    selected = []
    for frame_idx in sorted(stream_samples.keys()):
        indexed = {
            stream_idx: sample_path
            for stream_idx, sample_path in stream_samples[frame_idx]
        }
        selected_sample_paths = [
            indexed.get(stream_idx) for stream_idx in selected_stream_indices
        ]
        selected.append((frame_idx, selected_sample_paths))
    return selected
