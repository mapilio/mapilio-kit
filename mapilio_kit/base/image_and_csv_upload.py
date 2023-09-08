import argparse

class image_and_csv_upload:
    name = "image_and_csv_upload"
    help = "process panoramic images and upload to Mapilio"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        from . import loader, CSVprocesser
        CSVprocesser().fundamental_arguments(parser)
        loader().fundamental_arguments(parser)

    def perform_task(self, args: dict):
        from . import loader, CSVprocesser
        CSVprocesser().perform_task(args)
        loader().perform_task(args)
