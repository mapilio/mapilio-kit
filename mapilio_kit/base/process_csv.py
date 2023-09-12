from process_csv_to_description import process_csv_to_description
import argparse


class CSVprocess:
    name = "CSVprocessor"
    help = "create panorama csv to description format to Mapilio"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        group = parser.add_argument_group("upload options")
        group.add_argument(
            "--user_name", help="Upload to which Mapilio user account", required=False
        )
        group.add_argument(
            "--csv_path",
            help="Specify organization user name",
            default=None,
            required=False,
        )

    def filter_args(self, args):
        return {k: v for k, v in args.items() if k in process_csv_to_description.__code__.co_varnames}

    def perform_task(self, vars_args: dict):
        process_csv_to_description_args = self.filter_args(vars_args)
        process_csv_to_description(**process_csv_to_description_args)
