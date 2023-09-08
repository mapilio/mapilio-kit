import argparse
from gps_from_gopro360 import gopro360max_stitch


class gopro360max_process:
    name = "gopro360max_process"
    help = "Stitching GoProMax output format panoramic images"

    def fundamental_arguments(self, parser:argparse.ArgumentParser):
        group = parser.add_argument_group("upload options")
        group.add_argument('--video-file', '-vf', type=str, help='video file path', default=None)
        group.add_argument('--output-folder', '-of', type=str, help='output folder', default='/tmp/test')
        group.add_argument('--frame-rate', '-fps', type=int, help='how many frames to extract per frame', default=1)
        group.add_argument('--quality', '-q', type=int, help='frame extraction quality', default=2)
        group.add_argument('--bin-dir', '-b', type=str, help='directory that contains the MAX2spherebatch exec',
                           default='bin/')

    def filter_args(self, args):
        return {k: v for k, v in args.items() if k in gopro360max_stitch.__code__.co_varnames}

    def perform_task(self, vars_args: dict):
        stitch_args = self.filter_args(vars_args)
        gopro360max_stitch(**stitch_args)