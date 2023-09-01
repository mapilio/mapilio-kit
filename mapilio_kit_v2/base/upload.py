import argparse
class Upload:
    name = "upload"
    help = "upload images and descriptions to Mapilio"

    def add_basic_arguments(self, parser: argparse.ArgumentParser):

        group = parser.add_argument_group("upload options")
        group.add_argument(
            "--user_name", help="Upload to which Mapilio user account", required=False
        )

        group.add_argument(
            "--organization_username",
            help="Specify organization user name",
            default=None,
            required=False,
        )
        group.add_argument("--processed",
                                   action="store_true",
                                   help="processed option")

        group.add_argument(
            "--organization_key",
            help="Specify organization key",
            default=None,
            required=False,
        )
        group.add_argument(
            "--project_key",
            help="Specify project key",
            default=None,
            required=False,
        )
        group.add_argument(
            "--desc_path",
            help="Specify the path to read image description",
            default=None,
            required=False,
        )
        group.add_argument(
            "--dry_run",
            help="Disable actual upload. Used for debugging only",
            action="store_true",
            default=False,
            required=False,
        )

    def run(self, vars_args: dict):
        pass