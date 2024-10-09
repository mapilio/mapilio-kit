# pyre-ignore-all-errors[4]

import dataclasses
import itertools
import math
import typing as T
from enum import Enum, unique

WGS84_a = 6378137.0
WGS84_a_SQ = WGS84_a ** 2
WGS84_b = 6356752.314245
WGS84_b_SQ = WGS84_b ** 2


@dataclasses.dataclass(order=True)
class Point:
    # For reducing object sizes
    # dataclass(slots=True) not available until 3.10
    __slots__ = (
        "time",
        "lat",
        "lon",
        "alt",
        "angle",
    )
    time: float
    lat: float
    lon: float
    alt: T.Optional[float]
    angle: T.Optional[float]


@unique
class GPSFix(Enum):
    NO_FIX = 0
    FIX_2D = 2
    FIX_3D = 3


@dataclasses.dataclass
class PointWithFix(Point):
    gps_fix: T.Optional[GPSFix]
    gps_precision: T.Optional[float]
    gps_ground_speed: T.Optional[float]


def calculate_ecef_from_lla(lat: float, lon: float) -> T.Tuple[float, float, float]:
    """
    Compute ECEF XYZ from latitude, longitude and altitude.

    All using the WGS94 model.
    Altitude is the distance to the WGS94 ellipsoid.
    Check results here http://www.oc.nps.edu/oc2902w/coord/llhxyz.htm

    """
    lat = math.radians(lat)
    lon = math.radians(lon)
    cos_lat = math.cos(lat)
    sin_lat = math.sin(lat)
    L = 1.0 / math.sqrt(WGS84_a_SQ * cos_lat ** 2 + WGS84_b_SQ * sin_lat ** 2)
    K = WGS84_a_SQ * L * cos_lat
    x = K * math.cos(lon)
    y = K * math.sin(lon)
    z = WGS84_b_SQ * L * sin_lat
    return x, y, z


def calculate_gps_distance(
        latlon_1: T.Tuple[float, float], latlon_2: T.Tuple[float, float]
) -> float:
    """
    Distance between two (lat,lon) pairs.

    >>> p1 = (42.1, -11.1)
    >>> p2 = (42.2, -11.3)
    >>> 19000 < calculate_gps_distance(p1, p2) < 20000
    True
    """
    x1, y1, z1 = calculate_ecef_from_lla(latlon_1[0], latlon_1[1])
    x2, y2, z2 = calculate_ecef_from_lla(latlon_2[0], latlon_2[1])

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)


def determine_maximum_distance_from_start(latlons: T.List[T.Tuple[float, float]]) -> float:
    """
    Returns the radius of an entire GPS track. Used to calculate whether or not the entire sequence was just stationary video
    Takes a sequence of points as input
    """
    if not latlons:
        return 0
    start = latlons[0]
    return max(calculate_gps_distance(start, latlon) for latlon in latlons)


def compute_bearing(
        start_lat: float, start_lon: float, end_lat: float, end_lon: float
) -> float:
    """
    Get the compass bearing from start to end.

    Formula from
    http://www.movable-type.co.uk/scripts/latlong.html
    """
    # make sure everything is in radians
    start_lat = math.radians(start_lat)
    start_lon = math.radians(start_lon)
    end_lat = math.radians(end_lat)
    end_lon = math.radians(end_lon)

    dLong = end_lon - start_lon

    if abs(dLong) > math.pi:
        if dLong > 0.0:
            dLong = -(2.0 * math.pi - dLong)
        else:
            dLong = 2.0 * math.pi + dLong

    y = math.sin(dLong) * math.cos(end_lat)
    x = math.cos(start_lat) * math.sin(end_lat) - math.sin(start_lat) * math.cos(
        end_lat
    ) * math.cos(dLong)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

    return bearing


_IT = T.TypeVar("_IT")


# http://stackoverflow.com/a/5434936
def generate_pairs(iterable: T.Iterable[_IT]) -> T.Iterable[T.Tuple[_IT, _IT]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def _interpolate_segment(start: Point, end: Point, t: float) -> Point:
    if start.time == end.time:
        weight = 0.0
    else:
        weight = (t - start.time) / (end.time - start.time)

    lat = start.lat + (end.lat - start.lat) * weight
    lon = start.lon + (end.lon - start.lon) * weight
    angle = compute_bearing(start.lat, start.lon, end.lat, end.lon)
    alt: T.Optional[float]
    if start.alt is not None and end.alt is not None:
        alt = start.alt + (end.alt - start.alt) * weight
    else:
        alt = None

    return Point(time=t, lat=lat, lon=lon, alt=alt, angle=angle)


def _interpolate_at_index(points: T.Sequence[Point], t: float, idx: int):
    assert points, "expect non-empty points"

    # find the segment (start point, end point)
    if len(points) == 1:
        start, end = points[0], points[0]
    else:
        if 0 < idx < len(points):
            # interpolating within the range
            start, end = points[idx - 1], points[idx]
        elif idx <= 0:
            # extrapolating behind the range
            start, end = points[0], points[1]
        else:
            # extrapolating beyond the range
            assert len(points) <= idx
            start, end = points[-2], points[-1]

    return _interpolate_segment(start, end, t)


class Interpolator:
    """
    Interpolator for interpolating a sequence of timestamps incrementally.
    """

    tracks: T.Sequence[T.Sequence[Point]]
    track_idx: int
    # interpolation starts from the lower bound point index in the current track
    lo: int
    prev_time: T.Optional[float]

    def __init__(self, tracks: T.Sequence[T.Sequence[Point]]):
        self.tracks = [track for track in tracks if track]
        if not self.tracks:
            raise ValueError("Expect non-empty tracks")
        self.tracks.sort(key=lambda track: track[0].time)
        self.track_idx = 0
        self.lo = 0
        self.prev_time = None

    @staticmethod
    def _lsearch_left(
            track: T.Sequence[Point], t: float, lo: int = 0, hi: T.Optional[int] = None
    ) -> int:
        """
        similar to bisect.bisect_left, but faster in the incremental search case
        """
        assert 0 <= lo, "expect non-negative lower bound"
        if hi is None:
            hi = len(track)
        while lo < hi:
            # assert track[lo - 1].time < t
            if t <= track[lo].time:
                break
            # assert track[lo].time < t
            lo += 1
        # assert track[lo - 1].time < t <= track[lo].time
        return lo

    def interpolate(self, t: float) -> Point:
        if self.prev_time is not None:
            assert self.prev_time <= t, "requires time to be monotonically increasing"

        while self.track_idx < len(self.tracks):
            track = self.tracks[self.track_idx]
            if t < track[0].time:
                return _interpolate_at_index(track, t, 0)
            elif track[0].time <= t <= track[-1].time:
                # similar to bisect.bisect_left(points, p, lo=lo) but faster in this case
                idx = Interpolator._lsearch_left(track, t, lo=self.lo)
                # t must sit between (track[idx - 1], track[idx]]
                # set the lower bound to idx - 1
                # because the next t can still be interpolated anywhere between (track[idx - 1], track[idx]]
                self.lo = max(idx - 1, 0)
                return _interpolate_at_index(track, t, idx)
            self.track_idx += 1
            self.lo = 0

        interpolated = _interpolate_at_index(self.tracks[-1], t, len(self.tracks[-1]))

        self.prev_time = t

        return interpolated


_PointAbstract = T.TypeVar("_PointAbstract")


def filter_points_by_distance(
        samples: T.Iterable[_PointAbstract],
        min_distance: float,
        point_func: T.Callable[[_PointAbstract], Point],
) -> T.Generator[_PointAbstract, None, None]:
    prevp: T.Optional[Point] = None
    for sample in samples:
        if prevp is None:
            yield sample
            prevp = point_func(sample)
        else:
            p = point_func(sample)
            if min_distance < calculate_gps_distance((prevp.lat, prevp.lon), (p.lat, p.lon)):
                yield sample
                prevp = p


_PointLike = T.TypeVar("_PointLike", bound=Point)


def extend_deduplicate_points(
        sequence: T.Iterable[_PointLike],
        to_extend: T.Optional[T.List[_PointLike]] = None,
) -> T.List[_PointLike]:
    if to_extend is None:
        to_extend = []
    for point in sequence:
        if to_extend:
            prev = to_extend[-1].lon, to_extend[-1].lat
            cur = (point.lon, point.lat)
            if cur != prev:
                to_extend.append(point)
        else:
            to_extend.append(point)
    return to_extend
