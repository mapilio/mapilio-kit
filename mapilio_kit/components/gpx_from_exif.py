from types_fmt import GPXPoint, GPXPointAngle
from exif_metadata_reader import ExifRead
from error import MapilioGeoTaggingError


def gpx_from_exif(image: str) -> GPXPointAngle:
    exif = ExifRead(image)

    lon, lat = exif.calc_lon_lat()
    if lat is None or lon is None:
        raise MapilioGeoTaggingError(
            "Unable to extract GPS Longitude or GPS Latitude from the image"
        )

    timestamp = exif.extract_capture_time()
    if timestamp is None:
        raise MapilioGeoTaggingError("Unable to extract timestamp from the image")

    angle = exif.extract_direction()

    return GPXPointAngle(
        point=GPXPoint(
            time=timestamp,
            lon=lon,
            lat=lat,
            alt=exif.extract_altitude(),
        ),
        angle=angle,
    )
