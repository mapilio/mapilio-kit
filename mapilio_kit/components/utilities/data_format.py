class DataFormat:
    latitude: str
    longitude: str
    altitude: str
    captureTime: str
    roll: float
    pitch: float
    yaw: float
    heading: float
    sequenceUuid: str
    orientation: int
    deviceMake: str = "sony"
    deviceModel: str = "Ladybug"
    imageSize: str = "8192x4096"
    fov: str = "360"
    photoUuid: str
    imageName: str
    imagePath: str


class CsvFormat:
    OutputFileName: str = 'csv_out'
