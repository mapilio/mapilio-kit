import datetime
import sys
import typing as T

if sys.version_info >= (3, 8):
    from typing import TypedDict, Literal  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict, Literal


class User(TypedDict, total=False):
    OrganizationKey: str
    OrganizationProjectKey: str
    SettingsUsername: str
    SettingsUserKey: str
    user_upload_token: str


# class CompassHeading(TypedDict, total=True):
#     Heading: float
#     # MagneticHeading: float


class ImageRequired(TypedDict, total=True):
    latitude: float
    longitude: float
    captureTime: str


class Image(ImageRequired, total=False):
    altitude: float
    PhotoUUID: str
    Heading: float
    Roll: float
    Pitch: float


class _SequenceOnly(TypedDict, total=True):
    SequenceUUID: str


class Sequence(_SequenceOnly, total=False):
    Heading: float


class MetaProperties(TypedDict, total=False):
    MetaTags: T.Dict
    DeviceMake: str
    DeviceModel: str
    GPSAccuracyMeters: float
    CameraUUID: str
    Filename: str
    Path: str
    Orientation: int
    ImageSize: str
    FoV: int
    PhotoUUID: str
    acceleration: str
    gyroscope: str


class FinalImageDescription(_SequenceOnly, User, Image):
    pass


class ImageDescriptionJSON(FinalImageDescription):
    path: str
    filename: str


class FinalImageDescriptionError(TypedDict):
    path: str
    filename: str
    error: T.Dict


FinalImageDescriptionOrError = T.Union[
    FinalImageDescriptionError, FinalImageDescription
]


class FinalImageDescriptionFromGeoJSON(FinalImageDescription):
    pass


UserItemAttributes = {
    "type": "object",
    "properties": {
        "OrganizationKey": {"type": "string"},
        "OrganizationProjectKey": {"type": "string"},
        "SettingsUsername": {"type": "string"},
        "SettingsUserPassword": {"type": "string"},
        "SettingsUserKey": {"type": "string"},
        "user_upload_token": {"type": "string"},
    },
    "required": ["SettingsUserKey", "user_upload_token"],
    "additionalProperties": False,
}

FinalImageDescriptionMetadata = {
    "type": "object",
    "properties": {
        "latitude": {"type": "number", "description": "latitude of the image"},
        "longitude": {"type": "number", "description": "longitude of the image"},
        "altitude": {"type": "number", "description": "altitude of the image"},
        "captureTime": {
            "type": "string",
            "description": "Capture time of the image",
        },
        "photoUuid": {"type": "string"},
        "heading": {"type": "number"},
        "sequenceUuid": {
            "type": "string",
            "description": "Arbitrary key used to group images",
        },
        "deviceModel": {"type": "string"},
        "deviceMake": {"type": "string"},
        "cameraUuid": {"type": "string"},
        "imageSize": {"type": "string"},
        "fov": {"type": "number"},
        "anomaly": {"type": "number"},
        "yaw": {"type": "number"},
        "carSpeed": {"type": "number"},
        "pitch": {"type": "number"},
        "roll": {"type": "number"},
        "megapixels": {"type": "number"},
        "path": {"type": "string"},
        "filename": {"type": "string"},
        "orientation": {"type": "integer"},
        "acceleration": {"type": "string"},
        "gyroscope": {"type": "string"},
        "vfov": {"type": "number"},
        "accuracy_level": {"type": "number"},
        "source": {"type": "string"},
    },
    "required": [
        "latitude",
        "longitude",
        "captureTime",
    ],
    "additionalProperties": False,
}


def merge_schema(*schemas: T.Dict):
    for s in schemas:
        assert s.get("type") == "object", "must be all object schemas"
    properties = {}
    all_required = []
    additional_properties = True
    for s in schemas:
        properties.update(s.get("properties", {}))
        all_required += s.get("required", [])
        if "additionalProperties" in s:
            additional_properties = s["additionalProperties"]
    return {
        "type": "object",
        "properties": properties,
        "required": list(set(all_required)),
        "additionalProperties": additional_properties,
    }


ImageDescriptionJSONSchema = merge_schema(
    FinalImageDescriptionMetadata,
    {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The image file's path relative to the image directory",
            },
            "path": {
                "type": "string",
                "description": "The image base directory"
            },
        },
        "required": [
            "filename",
            "path",
        ],
    },
)

Process = Literal[
    "import_meta_data_process",
    "geotag_process",
    "sequence_process",
    "mapilio_image_description",
]

Status = Literal["success", "failed"]


def datetime_to_map_capture_time(time: datetime.datetime) -> str:
    # return datetime.datetime.strftime(time, "%Y-%m-%d  %H:%M:%S:%f")[:-3] # deprecated
    return datetime.datetime.strftime(time, "%Y-%m-%d %H:%M:%S")


def map_capture_time_to_datetime(time: str) -> datetime.datetime:
    # return datetime.datetime.strptime(time, "%Y_%m_%d_%H_%M_%S_%f") # deprecated
    return datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")


class GPXPoint(T.NamedTuple):
    # Put it first for sorting
    time: datetime.datetime
    lat: float
    lon: float
    alt: T.Optional[float]

    def as_desc(self) -> Image:
        desc: Image = {
            "latitude": self.lat,
            "longitude": self.lon,
            "captureTime": datetime_to_map_capture_time(self.time),
        }
        if self.alt is not None:
            desc["altitude"] = self.alt
        return desc


class GPXPointAngle(T.NamedTuple):
    point: GPXPoint
    angle: T.Optional[float]

    def as_desc(self) -> Image:
        desc = self.point.as_desc()
        if self.angle is not None:
            desc["heading"] = self.angle
        return desc


if __name__ == "__main__":
    import json

    print(json.dumps(ImageDescriptionJSONSchema, indent=4))