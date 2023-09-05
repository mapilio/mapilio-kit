class MapilioUserError(Exception):
    pass


class MapilioGeoTaggingError(MapilioUserError):
    pass


class MapilioDuplicationError(MapilioUserError):
    def __init__(self, message, desc):
        super().__init__(message)
        self.desc = desc
