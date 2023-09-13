import argparse


def general_arguments(parser, command):
    if command == "authenticate" or command == "gopro360max_process" or command == "run":
        return
    if command in ["sampler", "video_process", "video_upload"]:
        parser.add_argument(
            "video_import_path",
            help="Path to a video or directory with one or more video files.",
        )
        parser.add_argument(
            "import_path",
            help='Path to where the images from video sampling will be saved. If not specified, it will default to '
                 '"mapilio_sampled_video_frames" under your video import path',
            nargs="?",
        )
        parser.add_argument(
            "--skip_subfolders",
            help="Skip all subfolders and import only the images in the given video_import_path",
            action="store_true",
            default=False,
            required=False,
        )
    elif command in ["upload", "image_and_csv_upload"]:
        parser.add_argument(
            "import_path",
            help="Path to your images",
        )
    elif command in ["download"]:
        parser.add_argument(
            "download_path",
            help="Path to your images",
        )
    elif command in ["zip"]:
        parser.add_argument(
            "import_path",
            help="Path to your images",
        )
        parser.add_argument(
            "zip_dir",
            help="Path to store zipped images",
        )
    else:
        parser.add_argument(
            "import_path",
            help="Path to your images",
        )
        parser.add_argument(
            "--skip_subfolders",
            help="Skip all subfolders and import only the images in the given import_path",
            action="store_true",
            default=False,
            required=False,
        )