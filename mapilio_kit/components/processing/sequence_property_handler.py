import typing as T
import datetime
import os
import uuid

from mapilio_kit.components.logs import image_log
from mapilio_kit.components.utilities import types_fmt as types
from calculation.geospatial_utils import calculate_compass_bearing, gps_distance, generate_pairs
from mapilio_kit.components import version
from mapilio_kit.components.utilities.error import MapilioDuplicationError

MAX_SEQUENCE_LENGTH = 250


class _GPXPoint:
    desc: types.Image
    filename: str

    def __init__(self, desc: types.Image, filename: str):
        self.desc = desc
        self.filename = filename

    @property
    def lat(self) -> float:
        return self.desc["latitude"]

    @property
    def lon(self) -> float:
        return self.desc["longitude"]

    @property
    def time(self) -> datetime.datetime:
        return types.map_capture_time_to_datetime(self.desc["captureTime"])

    @property
    def angle(self) -> T.Optional[float]:
        return self.desc.get("heading")


Sequence = T.List[_GPXPoint]


def load_geotag_points(
    images: T.List[str],
) -> T.Generator[_GPXPoint, None, None]:
    for image in images:
        ret = image_log.read_process_data_from_memory(image, "geotag_process")
        if ret is None:
            continue
        status, geotag_data = ret
        if status != "success":
            continue
        yield _GPXPoint(T.cast(types.Image, geotag_data), image)


def split_sequences(
    sequence: Sequence,
    cutoff_distance: float,
    cutoff_time: float,
) -> T.List[Sequence]:
    sequences: T.List[T.List[_GPXPoint]] = []

    if sequence:
        sequences.append([sequence[0]])

    for prev, cur in generate_pairs(sequence):
        # invariant: prev is processed
        distance = gps_distance(
            (prev.lat, prev.lon),
            (cur.lat, cur.lon),
        )
        if cutoff_distance <= distance:
            sequences.append([cur])
            continue
        time_diff = (cur.time - prev.time).total_seconds()
        if cutoff_time <= time_diff:
            sequences.append([cur])
            continue
        sequences[-1].append(cur)
        # invariant: cur is processed

    return sequences


def find_duplicates(
    sequence: Sequence,
    duplicate_distance: float,
    duplicate_angle: float,
) -> T.List[int]:
    if not sequence:
        return []

    duplicates = []
    sequence_iter = iter(sequence)
    prev = next(sequence_iter)
    for idx, cur in enumerate(sequence_iter):
        distance = gps_distance(
            (prev.lat, prev.lon),
            (cur.lat, cur.lon),
        )
        distance_duplicated = False
        if distance <= duplicate_distance:
            distance_duplicated = True

        # Deprecated because of gps-anomaly do
        # if prev.angle is not None and cur.angle is not None:
        #     bearing_delta = diff_bearing(prev.angle, cur.angle)
        #     angle_duplicated = bearing_delta <= duplicate_angle
        # else:
        #     angle_duplicated = False

        if distance_duplicated:
            duplicates.append(idx + 1)
            continue

        prev = cur

    return duplicates


def sequence_property_handler(
    import_path,
    cutoff_distance=600.0,
    cutoff_time=60.0,
    interpolate_directions=False,
    duplicate_distance=0.1,
    duplicate_angle=5,
    skip_subfolders=False,
) -> None:
    if not import_path or not os.path.isdir(import_path):
        raise RuntimeError(f"Error, import directory {import_path} does not exist")
    sequences = find_sequences(import_path, skip_subfolders)
    for sequence in sequences:
        process_sequence_by_anomaly(
            sequence,
            cutoff_distance,
            cutoff_time,
            interpolate_directions,
            duplicate_distance,
            duplicate_angle,
        )

def process_sequence_by_anomaly(
        sequence: Sequence,
        cutoff_distance: float,
        cutoff_time: float,
        interpolate_directions: bool,
        duplicate_distance: float,
        duplicate_angle: float,
) -> None:
    splitted_sequences: T.List[Sequence] = split_sequences(
        sequence, cutoff_distance, cutoff_time
    )

    for sequence in splitted_sequences:
        _sequence = [
            image for idx, image in enumerate(sequence)
        ]
        

        # interpolate angles
        interpolated_dedup_sequence: Sequence = []
        for cur, nex in generate_pairs(_sequence):
            # should interpolate or not
            if interpolate_directions or cur.angle is None:
                new_bearing = calculate_compass_bearing(cur.lat, cur.lon, nex.lat, nex.lon)
                new_desc: types.Image = T.cast(
                    types.Image,
                    {
                        **cur.desc,
                        "heading": new_bearing
                    },
                )
                interpolated_dedup_sequence.append(_GPXPoint(new_desc, cur.filename))
            else:
                interpolated_dedup_sequence.append(cur)

        if interpolated_dedup_sequence:
            assert len(interpolated_dedup_sequence) == len(_sequence) - 1
        else:
            assert len(_sequence) <= 1

        # interpolate the last image's angle
        # can interpolate or not
        if 2 <= len(_sequence) and interpolated_dedup_sequence[-1] is not None:
            # should interpolate or not
            if interpolate_directions or _sequence[-1] is None:
                new_desc = T.cast(
                    types.Image,
                    {
                        **_sequence[-1].desc,
                        "heading": interpolated_dedup_sequence[-1].angle
                    },
                )
                interpolated_dedup_sequence.append(
                    _GPXPoint(new_desc, _sequence[-1].filename)
                )
            else:
                interpolated_dedup_sequence.append(_sequence[-1])
        else:
            interpolated_dedup_sequence.append(_sequence[-1])

        assert len(interpolated_dedup_sequence) == len(_sequence)

        # cut sequence per MAX_SEQUENCE_LENGTH images
        for idx in range(0, len(interpolated_dedup_sequence), MAX_SEQUENCE_LENGTH):
            sequence_uuid = str(uuid.uuid4())
            for image in interpolated_dedup_sequence[idx: idx + MAX_SEQUENCE_LENGTH]:
                desc: types.Sequence = {
                    "sequenceUuid": sequence_uuid,
                }
                heading = image.desc.get("heading")
                desc["source"] = f"Mapilio_Kit-v{version.VERSION}"
                if heading is not None:
                    desc["heading"] = heading
                image_log.log_in_memory(image.filename, "sequence_process", desc)

# Deprecated
def process_sequence_deprecated(
    sequence: Sequence,
    cutoff_distance: float,
    cutoff_time: float,
    interpolate_directions: bool,
    duplicate_distance: float,
    duplicate_angle: float,
) -> None:
    splitted_sequences: T.List[Sequence] = split_sequences(
        sequence, cutoff_distance, cutoff_time
    )

    for sequence in splitted_sequences:
        # duplication check
        dup_indices = find_duplicates(
            sequence,
            duplicate_distance=duplicate_distance,
            duplicate_angle=duplicate_angle,
        )
        dup_set = set(dup_indices)
        dup_sequence = [image for idx, image in enumerate(sequence) if idx in dup_set]
        for image in dup_sequence:
            image_log.log_failed_in_memory(
                image.filename,
                "sequence_process",
                MapilioDuplicationError("duplicated", image.desc),
            )

        dedup_sequence = [
            image for idx, image in enumerate(sequence) if idx not in dup_set
        ]

        # interpolate angles
        interpolated_dedup_sequence: Sequence = []
        for cur, nex in generate_pairs(dedup_sequence):
            # should interpolate or not
            if interpolate_directions or cur.angle is None:
                new_bearing = calculate_compass_bearing(cur.lat, cur.lon, nex.lat, nex.lon)
                new_desc: types.Image = T.cast(
                    types.Image,
                    {
                        **cur.desc,
                        "heading": new_bearing
                    },
                )
                interpolated_dedup_sequence.append(_GPXPoint(new_desc, cur.filename))
            else:
                interpolated_dedup_sequence.append(cur)

        if interpolated_dedup_sequence:
            assert len(interpolated_dedup_sequence) == len(dedup_sequence) - 1
        else:
            assert len(dedup_sequence) <= 1

        # interpolate the last image's angle
        # can interpolate or not
        if 2 <= len(dedup_sequence) and interpolated_dedup_sequence[-1] is not None:
            # should interpolate or not
            if interpolate_directions or dedup_sequence[-1] is None:
                new_desc = T.cast(
                    types.Image,
                    {
                        **dedup_sequence[-1].desc,
                        "heading": interpolated_dedup_sequence[-1].angle
                    },
                )
                interpolated_dedup_sequence.append(
                    _GPXPoint(new_desc, dedup_sequence[-1].filename)
                )
            else:
                interpolated_dedup_sequence.append(dedup_sequence[-1])
        else:
            interpolated_dedup_sequence.append(dedup_sequence[-1])

        assert len(interpolated_dedup_sequence) == len(dedup_sequence)

        # cut sequence per MAX_SEQUENCE_LENGTH images
        for idx in range(0, len(interpolated_dedup_sequence), MAX_SEQUENCE_LENGTH):
            sequence_uuid = str(uuid.uuid4())
            for image in interpolated_dedup_sequence[idx: idx + MAX_SEQUENCE_LENGTH]:
                desc: types.Sequence = {
                    "sequenceUuid": sequence_uuid,
                }
                heading = image.desc.get("heading")
                desc["source"] = f"Mapilio_Kit-v{version.VERSION}"
                if heading is not None:
                    desc["heading"] = heading
                image_log.log_in_memory(image.filename, "sequence_process", desc)


def find_sequences(
    import_path: str,
    skip_subfolders: bool,
) -> T.List[Sequence]:
    sort_key = lambda image: image.time

    if skip_subfolders:
        images = image_log.get_total_file_list(
            import_path,
            skip_subfolders=True,
        )
        sequence = sorted(list(load_geotag_points(images)), key=sort_key)
        return [sequence]
    else:
        sequences = []

        # sequence limited to the root of the files
        for root, dirs, files in os.walk(import_path, topdown=True):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            images = image_log.get_total_file_list(
                root,
                skip_subfolders=True,
            )
            sequence = sorted(list(load_geotag_points(images)), key=sort_key)
            sequences.append(sequence)

        return sequences
