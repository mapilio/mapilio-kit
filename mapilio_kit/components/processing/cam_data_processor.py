# pyre-ignore-all-errors[5, 11, 16, 21, 24, 58]

import dataclasses
import io
import typing as T
from enum import Enum

import construct as C

from mapilio_kit.components.blending import struct_blender as cparser, video_blender as sample_parser, \
    basics_blender as parser
from mapilio_kit.components.utilities import point as P_exe



# Camera Motion Metadata Spec https://developers.google.com/streetview/publish/camm-spec
class CameraMotionCategory(Enum):
    ANGLE_AXIS = 0
    EXPOSURE_TIME = 1
    GYRO = 2
    ACCELERATION = 3
    POSITION = 4
    MIN_GPS = 5
    GPS = 6
    MAGNETIC_FIELD = 7


# All fields are little-endian
Float = C.Float32l
Double = C.Float64l

_SWITCH: T.Dict[int, C.Struct] = {
    # angle_axis
    CameraMotionCategory.ANGLE_AXIS.value: Float[3],
    CameraMotionCategory.EXPOSURE_TIME.value: C.Struct(
        "pixel_exposure_time" / C.Int32sl,
        "rolling_shutter_skew_time" / C.Int32sl,
    ),
    # gyro
    CameraMotionCategory.GYRO.value: Float[3],
    # acceleration
    CameraMotionCategory.ACCELERATION.value: Float[3],
    # position
    CameraMotionCategory.POSITION.value: Float[3],
    # lat, lon, alt
    CameraMotionCategory.MIN_GPS.value: Double[3],
    CameraMotionCategory.GPS.value: C.Struct(
        "time_gps_epoch" / Double,
        "gps_fix_type" / C.Int32sl,
        "latitude" / Double,
        "longitude" / Double,
        "altitude" / Float,
        "horizontal_accuracy" / Float,
        "vertical_accuracy" / Float,
        "velocity_east" / Float,
        "velocity_north" / Float,
        "velocity_up" / Float,
        "speed_accuracy" / Float,
    ),
    # magnetic_field
    CameraMotionCategory.MAGNETIC_FIELD.value: Float[3],
}

CAMMSampleData = C.Struct(
    C.Padding(2),
    "type" / C.Int16ul,
    "data"
    / C.Switch(
        C.this.type,
        _SWITCH,
    ),
)


def _parse_point_from_sample(
        fp: T.BinaryIO, sample: sample_parser.Sample
) -> T.Optional[P_exe.Point]:
    fp.seek(sample.offset, io.SEEK_SET)
    data = fp.read(sample.size)
    box = CAMMSampleData.parse(data)
    if box.type == CameraMotionCategory.MIN_GPS.value:
        return P_exe.Point(
            time=sample.time_offset,
            lat=box.data[0],
            lon=box.data[1],
            alt=box.data[2],
            angle=None,
        )
    elif box.type == CameraMotionCategory.GPS.value:
        # Not using box.data.time_gps_epoch as the point timestamp
        # because it is from another clock
        return P_exe.Point(
            time=sample.time_offset,
            lat=box.data.latitude,
            lon=box.data.longitude,
            alt=box.data.altitude,
            angle=None,
        )
    return None


def filter_points_by_elst(
        points: T.Iterable[P_exe.Point], elst: T.Sequence[T.Tuple[float, float]]
) -> T.Generator[P_exe.Point, None, None]:
    empty_elst = [entry for entry in elst if entry[0] == -1]
    if empty_elst:
        offset = empty_elst[-1][1]
    else:
        offset = 0

    elst = [entry for entry in elst if entry[0] != -1]

    if not elst:
        for p in points:
            yield dataclasses.replace(p, time=p.time + offset)
        return

    elst.sort(key=lambda entry: entry[0])
    elst_idx = 0
    for p in points:
        if len(elst) <= elst_idx:
            break
        media_time, duration = elst[elst_idx]
        if p.time < media_time:
            pass
        elif p.time <= media_time + duration:
            yield dataclasses.replace(p, time=p.time + offset)
        else:
            elst_idx += 1


def elst_entry_to_seconds(
        entry: T.Dict, movie_timescale: int, media_timescale: int
) -> T.Tuple[float, float]:
    assert movie_timescale > 0, "expected positive movie_timescale"
    assert media_timescale > 0, "expected positive media_timescale"
    media_time, duration = entry["media_time"], entry["segment_duration"]
    if media_time != -1:
        media_time = media_time / media_timescale
    duration = duration / movie_timescale
    return (media_time, duration)


def _extract_camm_samples(
        s: T.BinaryIO,
        maxsize: int = -1,
) -> T.Generator[sample_parser.Sample, None, None]:
    samples = sample_parser.parse_samples_from_trak(s, maxsize=maxsize)
    camm_samples = (
        sample for sample in samples if sample.description["format"] == b"camm"
    )
    yield from camm_samples


def extract_points(fp: T.BinaryIO) -> T.Optional[T.List[P_exe.Point]]:
    """
    Return a list of points (could be empty) if it is a valid CAMM video,
    otherwise None
    """

    points = None
    movie_timescale = None
    media_timescale = None
    elst_entries = None

    for h, s in parser.parse_path(fp, [b"moov", [b"mvhd", b"trak"]]):
        if h.type == b"trak":
            trak_start_offset = s.tell()

            descriptions = sample_parser.parse_descriptions_from_trak(
                s, maxsize=h.maxsize
            )
            camm_descriptions = [d for d in descriptions if d["format"] == b"camm"]
            if camm_descriptions:
                s.seek(trak_start_offset, io.SEEK_SET)
                camm_samples = _extract_camm_samples(s, h.maxsize)

                points_with_nones = (
                    _parse_point_from_sample(fp, sample)
                    for sample in camm_samples
                    if sample.description["format"] == b"camm"
                )

                points = [p for p in points_with_nones if p is not None]
                if points:
                    s.seek(trak_start_offset)
                    elst_data = parser.parse_box_data_first(
                        s, [b"edts", b"elst"], maxsize=h.maxsize
                    )
                    if elst_data is not None:
                        elst_entries = cparser.EditBox.parse(elst_data)["entries"]

                    s.seek(trak_start_offset)
                    mdhd_data = parser.parse_box_data_firstx(
                        s, [b"mdia", b"mdhd"], maxsize=h.maxsize
                    )
                    mdhd = cparser.MediaHeaderBox.parse(mdhd_data)
                    media_timescale = mdhd["timescale"]
        else:
            assert h.type == b"mvhd"
            if not movie_timescale:
                mvhd = cparser.MovieHeaderBox.parse(s.read(h.maxsize))
                movie_timescale = mvhd["timescale"]

        # exit when both found
        if movie_timescale is not None and points:
            break

    if points and movie_timescale and media_timescale and elst_entries:
        segments = [
            elst_entry_to_seconds(entry, movie_timescale, media_timescale)
            for entry in elst_entries
        ]
        points = list(filter_points_by_elst(points, segments))

    return points


MakeOrModel = C.Struct(
    "size" / C.Int16ub,
    C.Padding(2),
    "data" / C.FixedSized(C.this.size, C.GreedyBytes),
)


def _decode_quietly(data: bytes, h: parser.Header) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def _parse_quietly(data: bytes, h: parser.Header) -> bytes:
    try:
        parsed = MakeOrModel.parse(data)
    except C.ConstructError:
        return b""
    return parsed["data"]


def extract_camera_make_and_model(fp: T.BinaryIO) -> T.Tuple[str, str]:
    header_and_stream = parser.parse_path(
        fp,
        [
            b"moov",
            b"udta",
            [
                # Insta360 Titan
                b"\xa9mak",
                b"\xa9mod",
                # RICHO THETA V
                b"@mod",
                b"@mak",
                # RICHO THETA V
                b"manu",
                b"modl",
            ],
        ],
    )

    make: T.Optional[str] = None
    model: T.Optional[str] = None

    try:
        for h, s in header_and_stream:
            data = s.read(h.maxsize)
            if h.type == b"\xa9mak":
                make_data = _parse_quietly(data, h)
                make_data = make_data.rstrip(b"\x00")
                make = _decode_quietly(make_data, h)
            elif h.type == b"\xa9mod":
                model_data = _parse_quietly(data, h)
                model_data = model_data.rstrip(b"\x00")
                model = _decode_quietly(model_data, h)
            elif h.type in [b"@mak", b"manu"]:
                make = _decode_quietly(data, h)
            elif h.type in [b"@mod", b"modl"]:
                model = _decode_quietly(data, h)
            # quit when both found
            if make and model:
                break
    except parser.ParsingError:
        pass

    if make:
        make = make.strip()
    if model:
        model = model.strip()
    return make or "", model or ""
