import io
import logging
import typing as T
from multiprocessing import Pool
import abc

from tqdm import tqdm

from mapilio_kit.components.utilities import point as P_exe, types_fmt as types
from mapilio_kit.components.processing import cam_data_processor
from mapilio_kit.components.geotagging import gopro_location_filter, gopro_parser
from mapilio_kit.components.blending import basics_blender as parser


class GenericVideoGeotagger(abc.ABC):
    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def to_description(self):
        raise NotImplementedError
class VideoGeotagHandler(GenericVideoGeotagger):
    def __init__(
        self,
        video_paths,
        filetypes = None,
        num_processes: T.Optional[int] = None,
    ):
        self.video_paths = video_paths
        self.filetypes = filetypes
        self.num_processes = num_processes

    def to_description(self):
        if self.num_processes is None:
            num_processes = self.num_processes
            disable_multiprocessing = False
        else:
            num_processes = max(self.num_processes, 1)
            disable_multiprocessing = self.num_processes <= 0

        with Pool(processes=num_processes) as pool:
            if disable_multiprocessing:
                video_metadatas_iter = map(self._geotag_video, self.video_paths)
            else:
                video_metadatas_iter = pool.imap(
                    self._geotag_video,
                    self.video_paths,
                )
            return list(
                tqdm(
                    video_metadatas_iter,
                    desc="Extracting GPS tracks from videos",
                    unit="videos",
                    total=len(self.video_paths),
                )
            )

    def _geotag_video(
        self,
        video_path,
    ):
        return VideoGeotagHandler.geotag_video(video_path, self.filetypes)

    @staticmethod
    def _extract_video_metadata(
        video_path,
        filetypes = None,
    ):
        if (
            filetypes is None
            or types.FileType.VIDEO in filetypes
            or types.FileType.CAMM in filetypes
        ):
            with video_path.open("rb") as fp:
                try:
                    points = cam_data_processor.extract_points(fp)
                except parser.ParsingError:
                    points = None

                if points is not None:
                    fp.seek(0, io.SEEK_SET)
                    make, model = cam_data_processor.extract_camera_make_and_model(fp)
                    return types.VideoMetadata(
                        filename=video_path,
                        md5sum=None,
                        filetype=types.FileType.CAMM,
                        points=points,
                        make=make,
                        model=model,
                    )

        if (
            filetypes is None
            or types.FileType.VIDEO in filetypes
            or types.FileType.GOPRO in filetypes
        ):
            with video_path.open("rb") as fp:
                try:
                    points_with_fix = gopro_parser.extract_points(fp)
                except parser.ParsingError:
                    points_with_fix = None

                if points_with_fix is not None:
                    fp.seek(0, io.SEEK_SET)
                    make, model = "GoPro", gopro_parser.extract_camera_model(fp)
                    return types.VideoMetadata(
                        filename=video_path,
                        md5sum=None,
                        filetype=types.FileType.GOPRO,
                        points=T.cast(T.List[P_exe.Point], points_with_fix),
                        make=make,
                        model=model,
                    )
        return None

    @staticmethod
    def geotag_video(
        video_path,
        filetypes= None,
    ):
        video_metadata = None
        try:
            video_metadata = VideoGeotagHandler._extract_video_metadata(
                video_path, filetypes
            )

            if video_metadata is None:
                raise Exception("No GPS data found from the video")

            if not video_metadata.points:
                raise Exception("Empty GPS data found")

            video_metadata.points = P_exe.extend_deduplicate_points(video_metadata.points)
            assert video_metadata.points, "must have at least one point"

            if all(isinstance(p, P_exe.PointWithFix) for p in video_metadata.points):
                video_metadata.points = T.cast(
                    T.List[P_exe.Point],
                    gopro_location_filter.cleanse_noisy_points(
                        T.cast(T.List[P_exe.PointWithFix], video_metadata.points)
                    ),
                )
                if not video_metadata.points:
                    raise Exception("GPS is too noisy")

            stationary = P_exe.determine_maximum_distance_from_start([(p.lat, p.lon) for p in video_metadata.points]) < 10
            if stationary:
                raise Exception("Stationary video")

            video_metadata.update_md5sum()
        except Exception as ex:
            filetype = None if video_metadata is None else video_metadata.filetype
            return types.describe_error_metadata(
                ex,
                video_path,
                filetype=filetype,
            )

        return video_metadata
