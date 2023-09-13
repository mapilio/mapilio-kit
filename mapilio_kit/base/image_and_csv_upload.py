import argparse

class image_and_csv_upload:
    name = "image_and_csv_upload"
    help = "process panoramic images and upload to Mapilio"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        from . import uploader, CSVprocessor
        CSVprocessor().fundamental_arguments(parser)
        uploader().fundamental_arguments(parser)

    def perform_task(self, args: dict):
        from . import uploader, CSVprocessor
        CSVprocessor().perform_task(args)
        uploader().perform_task(args)
