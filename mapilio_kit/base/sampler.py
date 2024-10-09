import os
import argparse
from mapilio_kit.components.processing.video_processor import video_sampler


class Sampler:
    name = "Sampler"
    help = "sample video into images"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("video process options")
        group.add_argument(
            "--video_sample_interval",
            help="Time interval for sampled video frames in seconds",
            default=2,
            type=float,
            required=False,
        )
        group.add_argument(
            "--video_duration_ratio",
            help="Real time video duration ratio of the under or oversampled video duration.",
            type=float,
            default=1.0,
            required=False,
        )
        group.add_argument(
            "--video_start_time",
            help="Video start time in epochs (milliseconds)",
            type=int,
            default=None,
            required=False,
        )
        group.add_argument(
            "--skip_subfolders",
            help="Skip all subfolders and import only the images in the given directory path.",
            action="store_true",
            default=False,
            required=False,
        )
        group.add_argument(
            "--video_sample_distance",
            help="The distance of video sampling parameters",
            type=float,
            default=5.0,
        )
    def filter_args(self, args):
        return {k: v for k, v in args.items() if k in video_sampler.__code__.co_varnames}

    def perform_task(self, vars_args: dict):
        video_import_path = vars_args.get("video_import_path")
        import_path = vars_args.get("import_path")

        if import_path is None:
            if os.path.isdir(video_import_path):
                import_path = os.path.join(video_import_path, "mapilio_sampled_video_frames")
            else:
                import_path = os.path.join(os.path.dirname(video_import_path), "mapilio_sampled_video_frames")
            vars_args["import_path"] = import_path

        video_sampler_args = self.filter_args(vars_args)
        video_sampler(**video_sampler_args)