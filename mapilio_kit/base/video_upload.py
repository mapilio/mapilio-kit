import argparse
import os
from copy import deepcopy

class VideoUpload:
    name = "video_upload"
    help = "sample video into images, process the images and upload to Mapilio"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        from . import uploader, sampler
        sampler().fundamental_arguments(parser)
        uploader().fundamental_arguments(parser)

    def perform_task(self, vars_args: dict):
        from . import uploader, sampler
        video_paths = os.listdir(vars_args["video_import_path"]) if os.path.isdir(vars_args["video_import_path"]) else [vars_args["video_import_path"]]
        video_formats = ('.mp4', '.avi', '.mov', '.mkv', '.360', '.MP4', '.AVI', '.MOV', '.MKV')

        vars_args_copy=deepcopy(vars_args)
        for video_path in video_paths:
            vars_args_copy["video_import_path"] = os.path.join(vars_args["video_import_path"],video_path)
            if vars_args_copy["video_import_path"].endswith(video_formats):
                if not vars_args_copy['processed']:
                    sampler().perform_task(vars_args_copy)
                else:
                    vars_args_copy["import_path"] = vars_args_copy["video_import_path"]
                uploader().perform_task(vars_args_copy)
