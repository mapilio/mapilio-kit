import logging
import typing as T
import statistics

from mapilio_kit.components.utilities import point as P_exe
from mapilio_kit.components.logger import MapilioLogger

LOG = MapilioLogger().get_logger()

GOPRO_GPS_PRECISION = 15
GOPRO_GPS_FIXES = {0, 2, 3}
GOPRO_MAX_DOP100 =  1000

def purge_outliers(
    sequence: T.Sequence[P_exe.PointWithFix],
) -> T.Sequence[P_exe.PointWithFix]:
    distances = [
        P_exe.calculate_gps_distance((left.lat, left.lon), (right.lat, right.lon))
        for left, right in P_exe.generate_pairs(sequence)
    ]
    if len(distances) < 2:
        return sequence

    max_distance = calculate_upper_limit(distances)
    LOG.debug("max distance: %f", max_distance)
    max_distance = max(
        # distance between two points hence double
        GOPRO_GPS_PRECISION + GOPRO_GPS_PRECISION,
        max_distance,
    )
    sequences = divide_sequence_if(
        T.cast(T.List[P_exe.Point], sequence),
        distance_gt(max_distance),
    )
    LOG.debug(
        "Split to %d sequences with max distance %f", len(sequences), max_distance
    )

    ground_speeds = [
        p.gps_ground_speed for p in sequence if p.gps_ground_speed is not None
    ]
    if len(ground_speeds) < 2:
        return sequence

    max_speed = calculate_upper_limit(ground_speeds)
    merged = cluster_points(sequences, check_speed_below(max_speed))


    return T.cast(
        T.List[P_exe.PointWithFix],
        find_dominant_sequence(merged.values()),
    )


def cleanse_noisy_points(
    sequence: T.Sequence[P_exe.PointWithFix],
) -> T.Sequence[P_exe.PointWithFix]:
    num_points = len(sequence)
    sequence = [
        p
        for p in sequence
        # include points **without** GPS fix
        if p.gps_fix is None or p.gps_fix.value in GOPRO_GPS_FIXES
    ]
    if len(sequence) < num_points:
        LOG.debug(
            "Removed %d points with the GPS fix not in %s",
            num_points - len(sequence),
            GOPRO_GPS_FIXES,
        )

    num_points = len(sequence)
    sequence = [
        p
        for p in sequence
        # include points **without** precision
        if p.gps_precision is None or p.gps_precision <= GOPRO_MAX_DOP100
    ]
    if len(sequence) < num_points:
        LOG.debug(
            "Removed %d points with DoP value higher than %d",
            num_points - len(sequence),
            GOPRO_MAX_DOP100,
        )

    num_points = len(sequence)
    sequence = purge_outliers(sequence)
    if len(sequence) < num_points:
        LOG.debug(
            "Removed %d outlier points",
            num_points - len(sequence),
        )

    return sequence



PointSequence = T.List[P_exe.Point]
Decider = T.Callable[[P_exe.Point, P_exe.Point], bool]


def estimate_ground_speed(p1: P_exe.Point, p2: P_exe.Point) -> float:
    """
    Calculate the ground speed between two points (from p1 to p2).
    """
    s = P_exe.calculate_gps_distance((p1.lat, p1.lon), (p2.lat, p2.lon))
    t = abs(p2.time - p1.time)
    try:
        return s / t
    except ZeroDivisionError:
        return float("inf") if 0 <= s else float("-inf")


def calculate_upper_limit(values: T.Sequence[float]) -> float:
    """
    Calculate the upper whisker (i.e. Q3 + IRQ * 1.5) of the input values.
    Values larger than it are considered as outliers.
    See https://en.wikipedia.org/wiki/Interquartile_range
    """

    values = sorted(values)
    n = len(values)
    if n < 2:
        raise statistics.StatisticsError("at least 2 values are required for IQR")
    median_idx = n // 2
    q1 = statistics.median(values[:median_idx])
    if n % 2 == 1:
        # for values [0, 1, 2, 3, 4], q3 will be [3, 4]
        q3 = statistics.median(values[median_idx + 1 :])
    else:
        # for values [0, 1, 2, 3], q3 will be [2, 3]
        q3 = statistics.median(values[median_idx:])
    irq = q3 - q1
    return q3 + irq * 1.5


def divide_sequence_if(
    points: PointSequence,
    split_or_not: Decider,
) -> T.List[PointSequence]:
    if not points:
        return []

    sequences: T.List[PointSequence] = []
    for idx, point in enumerate(points):
        if sequences and not split_or_not(points[idx - 1], point):
            sequences[-1].append(point)
        else:
            sequences.append([point])
    assert len(points) == sum(len(g) for g in sequences)

    return sequences


def distance_gt(
    max_distance: float,
) -> Decider:
    """Return a callable that checks if two points are farther than the given distance."""

    def _split_or_not(p1, p2):
        distance = P_exe.calculate_gps_distance((p1.lat, p1.lon), (p2.lat, p2.lon))
        return distance > max_distance

    return _split_or_not


def check_speed_below(max_speed: float) -> Decider:
    """Return a callable that checks if the speed between two points are slower than the given speed."""

    def _split_or_not(p1, p2):
        speed = estimate_ground_speed(p1, p2)
        return speed <= max_speed

    return _split_or_not


def cluster_points(
    sequences: T.Sequence[PointSequence],
    merge_or_not: Decider,
) -> T.Dict[int, PointSequence]:
    """
    One-dimension DBSCAN clustering: https://en.wikipedia.org/wiki/DBSCAN
    The input is a list of sequences, and it is guaranteed that all sequences are sorted by time.
    The function clusters sequences by checking if two sequences can be merged or not.

    - minPoints is always 1
    - merge_or_not decides if two points are in the same cluster
    """

    # find which sequences (keys) should be merged to which sequences (values)
    mergeto: T.Dict[int, int] = {}
    for left in range(len(sequences)):
        mergeto.setdefault(left, left)
        # find the first sequence to merge with
        for right in range(left + 1, len(sequences)):
            if right in mergeto:
                continue
            if merge_or_not(sequences[left][-1], sequences[right][0]):
                mergeto[right] = mergeto[left]
                break

    # merge
    merged: T.Dict[int, PointSequence] = {}
    for idx, s in enumerate(sequences):
        merged.setdefault(mergeto[idx], []).extend(s)

    return merged


def find_dominant_sequence(sequences: T.Collection[PointSequence]) -> PointSequence:
    return sorted(sequences, key=lambda g: len(g), reverse=True)[0]