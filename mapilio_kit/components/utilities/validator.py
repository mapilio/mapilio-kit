"""Pre-flight EXIF/GPS validator used by ``mapilio_kit validate``.

This module deliberately performs *only* read-only inspection of images and
does not modify or upload anything. It produces a structured report that the
CLI wrapper turns into text or JSON.

Heavy dependencies (e.g. PIL/exiftool) are imported lazily inside helpers so
unit tests can run without installing them, and so importing this module
stays cheap.
"""

from __future__ import annotations

import math
import os
import typing as T
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

#: File extensions we consider candidates for validation.
IMAGE_EXTENSIONS: T.FrozenSet[str] = frozenset({
    ".jpg", ".jpeg", ".png", ".tif", ".tiff",
})

#: Thresholds used by the default validation rules. The CLI exposes overrides.
MAX_GPS_GAP_METERS: float = 5_000.0  # warn when consecutive points are >5km apart
MIN_TIME_GAP_SECONDS: float = 0.0    # timestamps should not go backwards
MAX_TIME_GAP_SECONDS: float = 3_600.0  # warn when consecutive captures >1h apart
SUSPICIOUS_LATLON: T.Tuple[float, float] = (0.0, 0.0)


@dataclass
class ImageRecord:
    """Minimal per-image metadata used by the validator."""

    path: str
    lat: T.Optional[float] = None
    lon: T.Optional[float] = None
    captured_at: T.Optional[float] = None  # epoch seconds, UTC
    error: T.Optional[str] = None


@dataclass
class Issue:
    """A single problem found during validation."""

    level: str  # "error" or "warning"
    code: str
    path: T.Optional[str]
    message: str
    details: T.Dict[str, T.Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    image_count: int
    valid_count: int
    issues: T.List[Issue]
    summary: T.Dict[str, int]

    @property
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.level == "warning" for i in self.issues)

    def to_dict(self) -> T.Dict[str, T.Any]:
        return {
            "image_count": self.image_count,
            "valid_count": self.valid_count,
            "summary": self.summary,
            "issues": [asdict(i) for i in self.issues],
        }


# --------------------------------------------------------------------------- #
# Discovery                                                                   #
# --------------------------------------------------------------------------- #


def find_images(
    root: str,
    *,
    skip_subfolders: bool = False,
    extensions: T.Iterable[str] = IMAGE_EXTENSIONS,
) -> T.List[str]:
    """Return a sorted list of image paths under ``root``."""
    exts = {e.lower() for e in extensions}
    if not os.path.isdir(root):
        return []
    found: T.List[str] = []
    if skip_subfolders:
        for entry in os.listdir(root):
            full = os.path.join(root, entry)
            if os.path.isfile(full) and os.path.splitext(entry)[1].lower() in exts:
                found.append(full)
    else:
        for dirpath, _dirs, filenames in os.walk(root):
            for fname in filenames:
                if os.path.splitext(fname)[1].lower() in exts:
                    found.append(os.path.join(dirpath, fname))
    return sorted(found)


# --------------------------------------------------------------------------- #
# EXIF reading                                                                #
# --------------------------------------------------------------------------- #


def _dms_to_decimal(dms: T.Sequence[T.Any], ref: str) -> float:
    """Convert ((d, m, s), ref) to a signed decimal degree."""
    deg, minutes, seconds = (float(x) for x in dms[:3])
    value = deg + minutes / 60.0 + seconds / 3600.0
    if ref in ("S", "W"):
        value = -value
    return value


def _parse_exif_datetime(text: str) -> T.Optional[float]:
    """Parse the standard EXIF DateTime ``YYYY:MM:DD HH:MM:SS`` format."""
    text = text.strip()
    fmts = (
        "%Y:%m:%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    )
    for fmt in fmts:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
    return None


def read_image_exif(
    path: str,
    *,
    exif_reader: T.Optional[T.Callable[[T.IO[bytes]], T.Mapping[str, T.Any]]] = None,
) -> ImageRecord:
    """Extract GPS + timestamp from a single image.

    ``exif_reader`` is injectable so unit tests can drive the function without
    a real exif backend. If omitted, ``ExifRead`` is loaded lazily.
    """
    if exif_reader is None:
        try:
            import exifread

            def _default_reader(fp: T.IO[bytes]) -> T.Mapping[str, T.Any]:
                return exifread.process_file(fp, details=False)

            exif_reader = _default_reader
        except ImportError:
            return ImageRecord(path=path, error="exifread not installed")

    try:
        with open(path, "rb") as fp:
            tags = exif_reader(fp)
    except OSError as exc:
        return ImageRecord(path=path, error=f"open failed: {exc}")
    except Exception as exc:  # noqa: BLE001 - exifread can raise odd errors
        return ImageRecord(path=path, error=f"exif read failed: {exc}")

    record = ImageRecord(path=path)

    lat_tag = tags.get("GPS GPSLatitude")
    lat_ref = tags.get("GPS GPSLatitudeRef")
    lon_tag = tags.get("GPS GPSLongitude")
    lon_ref = tags.get("GPS GPSLongitudeRef")
    if lat_tag and lat_ref and lon_tag and lon_ref:
        try:
            lat_values = [v.num / v.den for v in lat_tag.values]
            lon_values = [v.num / v.den for v in lon_tag.values]
            record.lat = _dms_to_decimal(lat_values, str(lat_ref))
            record.lon = _dms_to_decimal(lon_values, str(lon_ref))
        except (AttributeError, TypeError, ZeroDivisionError):
            # Some EXIF parsers return plain floats already; fall back.
            try:
                record.lat = _dms_to_decimal(list(lat_tag.values), str(lat_ref))
                record.lon = _dms_to_decimal(list(lon_tag.values), str(lon_ref))
            except Exception:  # noqa: BLE001
                pass

    for time_key in ("EXIF DateTimeOriginal", "Image DateTime", "EXIF DateTimeDigitized"):
        time_tag = tags.get(time_key)
        if time_tag is None:
            continue
        ts = _parse_exif_datetime(str(time_tag))
        if ts is not None:
            record.captured_at = ts
            break

    return record


# --------------------------------------------------------------------------- #
# Rules                                                                       #
# --------------------------------------------------------------------------- #


def _haversine_meters(p1: T.Tuple[float, float], p2: T.Tuple[float, float]) -> float:
    """Great-circle distance between two (lat, lon) pairs, in metres."""
    r = 6_371_000.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def validate_records(
    records: T.Sequence[ImageRecord],
    *,
    max_gap_meters: float = MAX_GPS_GAP_METERS,
    max_time_gap_seconds: float = MAX_TIME_GAP_SECONDS,
) -> T.List[Issue]:
    """Apply per-image and sequence-level rules, returning a list of issues."""
    issues: T.List[Issue] = []

    valid_pairs: T.List[T.Tuple[ImageRecord, float, float, float]] = []

    for rec in records:
        if rec.error:
            issues.append(Issue(
                level="error",
                code="exif_read_error",
                path=rec.path,
                message=rec.error,
            ))
            continue
        if rec.lat is None or rec.lon is None:
            issues.append(Issue(
                level="error",
                code="missing_gps",
                path=rec.path,
                message="Image has no GPS tags",
            ))
            continue
        if (rec.lat, rec.lon) == SUSPICIOUS_LATLON:
            issues.append(Issue(
                level="warning",
                code="suspicious_gps_zero",
                path=rec.path,
                message="GPS coordinates are exactly (0, 0)",
                details={"lat": rec.lat, "lon": rec.lon},
            ))
        if not (-90.0 <= rec.lat <= 90.0 and -180.0 <= rec.lon <= 180.0):
            issues.append(Issue(
                level="error",
                code="invalid_gps",
                path=rec.path,
                message=f"GPS coordinates out of range: ({rec.lat}, {rec.lon})",
                details={"lat": rec.lat, "lon": rec.lon},
            ))
            continue
        if rec.captured_at is None:
            issues.append(Issue(
                level="error",
                code="missing_timestamp",
                path=rec.path,
                message="Image has no EXIF capture time",
            ))
            continue
        valid_pairs.append((rec, rec.lat, rec.lon, rec.captured_at))

    # Sequence-level checks: walk in capture-time order.
    valid_pairs.sort(key=lambda x: x[3])

    seen_keys: T.Dict[T.Tuple[float, float, float], str] = {}
    for rec, lat, lon, t in valid_pairs:
        key = (round(lat, 6), round(lon, 6), round(t, 1))
        if key in seen_keys:
            issues.append(Issue(
                level="warning",
                code="duplicate_capture",
                path=rec.path,
                message=f"Same lat/lon/time as {seen_keys[key]}",
                details={"duplicate_of": seen_keys[key]},
            ))
        else:
            seen_keys[key] = rec.path

    for prev, curr in zip(valid_pairs, valid_pairs[1:]):
        prev_rec, prev_lat, prev_lon, prev_t = prev
        curr_rec, curr_lat, curr_lon, curr_t = curr
        if curr_t < prev_t:  # already sorted, but defensive
            continue
        time_gap = curr_t - prev_t
        if time_gap > max_time_gap_seconds:
            issues.append(Issue(
                level="warning",
                code="large_time_gap",
                path=curr_rec.path,
                message=(
                    f"{time_gap:.0f}s since previous image "
                    f"(threshold {max_time_gap_seconds:.0f}s)"
                ),
                details={"previous": prev_rec.path, "gap_seconds": time_gap},
            ))
        gap = _haversine_meters((prev_lat, prev_lon), (curr_lat, curr_lon))
        if gap > max_gap_meters:
            issues.append(Issue(
                level="warning",
                code="large_gps_gap",
                path=curr_rec.path,
                message=(
                    f"{gap:.0f} m from previous image "
                    f"(threshold {max_gap_meters:.0f} m)"
                ),
                details={"previous": prev_rec.path, "gap_meters": gap},
            ))

    return issues


def build_report(records: T.Sequence[ImageRecord], issues: T.List[Issue]) -> ValidationReport:
    summary: T.Dict[str, int] = {}
    for issue in issues:
        summary[issue.code] = summary.get(issue.code, 0) + 1
    paths_with_errors = {i.path for i in issues if i.level == "error" and i.path}
    valid_count = sum(1 for r in records if r.path not in paths_with_errors)
    return ValidationReport(
        image_count=len(records),
        valid_count=valid_count,
        issues=issues,
        summary=summary,
    )


def render_text(report: ValidationReport) -> str:
    lines: T.List[str] = ["Mapilio Kit validation report", "-" * 30]
    lines.append(f"  images       : {report.image_count}")
    lines.append(f"  valid (ready): {report.valid_count}")
    if report.summary:
        lines.append("  issues       :")
        for code, count in sorted(report.summary.items()):
            lines.append(f"    - {code:<24} {count}")
    else:
        lines.append("  issues       : none")
    if report.issues:
        lines.append("")
        lines.append("Details (first 20):")
        for issue in report.issues[:20]:
            tag = "ERROR" if issue.level == "error" else "WARN "
            path = issue.path or "-"
            lines.append(f"  [{tag}] {issue.code}  {path}")
            lines.append(f"         {issue.message}")
    return "\n".join(lines)
