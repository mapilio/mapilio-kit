import datetime
import math
import itertools
import bisect

from typing import List, Tuple, TypeVar, Iterable, Optional, NamedTuple

WGS84_a = 6378137.0
WGS84_b = 6356752.314245


def lla_to_ecef(lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
    """
    Convert Latitude, Longitude, and Altitude (LLA) coordinates to Earth-Centered, Earth-Fixed (ECEF) coordinates.

    Args:
        lat (float): Latitude in degrees.
        lon (float): Longitude in degrees.
        alt (float): Altitude above the ellipsoid in meters.

    Returns:
        Tuple[float, float, float]: ECEF XYZ coordinates (X, Y, Z) in meters.
    """
    # Convert latitude and longitude from degrees to radians
    lat = math.radians(lat)
    lon = math.radians(lon)

    # Square of the semi-major and semi-minor axes
    a2 = WGS84_a ** 2
    b2 = WGS84_b ** 2

    # Calculate eccentricity squared
    e2 = (a2 - b2) / a2

    # Calculate radius of curvature in the prime vertical
    N = WGS84_a / math.sqrt(1 - e2 * math.sin(lat) ** 2)

    # Calculate ECEF coordinates
    x = (N + alt) * math.cos(lat) * math.cos(lon)
    y = (N + alt) * math.cos(lat) * math.sin(lon)
    z = ((1 - e2) * N + alt) * math.sin(lat)

    return x, y, z

def calculate_bearing_difference(b1, b2):
    """
    Compute difference between two bearings
    """
    difference = abs(bearing2 - bearing1)
    difference = 360 - difference if difference > 180 else difference
    return difference

_IT = TypeVar("_IT")

# http://stackoverflow.com/a/5434936
def generate_pairs(iterable: Iterable) -> Iterable[Tuple]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    iterator = iter(iterable)
    try:
        prev_item = next(iterator)
    except StopIteration:
        return  # Empty iterable, so there are no pairs to generate.

    for item in iterator:
        yield (prev_item, item)
        prev_item = item


def gps_distance(latlon_1: Tuple[float, float], latlon_2: Tuple[float, float]) -> float:
    """
    Distance between two (lat,lon) pairs.

    >>> p1 = (42.1, -11.1)
    >>> p2 = (42.2, -11.3)
    >>> 19000 < gps_distance(p1, p2) < 20000
    True
    """
    x1, y1, z1 = lla_to_ecef(latlon_1[0], latlon_1[1], 0.0)
    x2, y2, z2 = lla_to_ecef(latlon_2[0], latlon_2[1], 0.0)

    dis = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

    return dis

def decimal_to_dms(value, precision):
    """
    Convert decimal position to degrees, minutes, seconds in a fromat supported by EXIF
    """
    deg = math.floor(value)
    min = math.floor((value - deg) * 60)
    sec = math.floor((value - deg - min / 60) * 3600 * precision)

    return (deg, 1), (min, 1), (sec, precision)

def calculate_compass_bearing(start_lat, start_lon, end_lat, end_lon) -> float:
    """
    Calculate the compass bearing from start to end coordinates.

    Formula sourced from
    http://www.movable-type.co.uk/scripts/latlong.html
    """
    # Ensure all coordinates are in radians
    start_lat = math.radians(start_lat)
    start_lon = math.radians(start_lon)
    end_lat = math.radians(end_lat)
    end_lon = math.radians(end_lon)

    delta_lon = end_lon - start_lon

    if abs(delta_lon) > math.pi:
        if delta_lon > 0.0:
            delta_lon = -(2.0 * math.pi - delta_lon)
        else:
            delta_lon = 2.0 * math.pi + delta_lon

    y = math.sin(delta_lon) * math.cos(end_lat)
    x = math.cos(start_lat) * math.sin(end_lat) - math.sin(start_lat) * math.cos(end_lat) * math.cos(delta_lon)
    bearing =math.degrees(math.atan2(y, x))
    # Convert the bearing to a compass bearing (0 to 360 degrees)
    compass_bearing = (bearing + 360) % 360

    return compass_bearing



_IT = TypeVar("_IT")


class Point(NamedTuple):
    time: datetime.datetime
    lat: float
    lon: float
    alt: Optional[float]


def interpolate_lat_lon(points: List[Point], t: datetime.datetime):
    if not points:
        raise ValueError("Expect non-empty points")
    # Make sure that points are sorted:
    # for cur, nex in pairwise(points):
    #     assert cur.time <= nex.time, "Points not sorted"
    idx = bisect.bisect_left([x.time for x in points], t)

    if 0 < idx < len(points):
        before = points[idx - 1]
        after = points[idx]
    elif idx <= 0:
        if 2 <= len(points):
            before, after = points[0], points[1]
        else:
            before, after = points[0], points[0]
    else:
        assert len(points) <= idx
        if 2 <= len(points):
            before, after = points[-2], points[-1]
        else:
            before, after = points[-1], points[-1]

    if before.time == after.time:
        weight = 0.0
    else:
        weight = (t - before.time).total_seconds() / (
            after.time - before.time
        ).total_seconds()
    lat = before.lat - weight * before.lat + weight * after.lat
    lon = before.lon - weight * before.lon + weight * after.lon
    bearing = calculate_compass_bearing(before.lat, before.lon, after.lat, after.lon)
    if before.alt is not None and after.alt is not None:
        alt: Optional[float] = before.alt - weight * before.alt + weight * after.alt
    else:
        alt = None
    return lat, lon, bearing, alt


def normalize_bearing(bearing: float, check_hex: bool = False) -> float:
    """
    Normalize bearing and convert from hex if
    """
    if bearing > 360 and check_hex:
        # fix negative value wrongly parsed in exifread
        # -360 degree -> 4294966935 when converting from hex
        bearing1 = bin(int(bearing))[2:]
        bearing2 = "".join([str(int(int(a) == 0)) for a in bearing1])
        bearing = -float(int(bearing2, 2))
    bearing %= 360
    return bearing