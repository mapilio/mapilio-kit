import argparse
from upload import zip_images


class Zip:
    name = "zip"
    help = "Zip images into sequences"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--desc_path",
            help="Specify the path to read image description",
            default=None,
            required=False,
        )
    def filter_args(self, args):
        return {k: v for k, v in args.items() if k in zip_images.__code__.co_varnames}
    def perform_task(self, vars_args: dict):
        return zip_images(**self.filter_args(vars_args))
