import argparse
import os
from ..components.export import export

class image_and_csv_upload:
    name = "image_and_csv_upload"
    help = "process panoramic images and upload to Mapilio"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        from . import uploader, CSVprocessor
        CSVprocessor().fundamental_arguments(parser)
        uploader().fundamental_arguments(parser)

    def perform_task(self, args: dict):
        from . import uploader, CSVprocessor
        export(
            csv_path = args["csv_path"],
            images_dir = args["import_path"],
            output_csv_name = os.path.join(args["import_path"], "out.csv")
        )
        args["csv_path"] = os.path.join(args["import_path"], "out.csv")
        args["processed"] = True
        CSVprocessor().perform_task(args)
        uploader().perform_task(args)

