import argparse
from edit_config import edit_config

class Authenticate:
    name = "authenticate"
    help = "authenticate Mapilio users"

    def fundamental_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--config_file",
            help="Full path to the config file to be edited. Default is ~/.config/mapilio/configs/MLY_CLIENT_ID",
            default=None,
            required=False,
        )
        parser.add_argument(
            "--user_name", help="Mapilio user name", default=None, required=False
        )
        parser.add_argument(
            "--user_email",
            help="user email, used to create Mapilio account",
            default=None,
            required=False,
        )
        parser.add_argument(
            "--user_password",
            help="password associated with the Mapilio user account",
            default=None,
            required=False,
        )
        parser.add_argument(
            "--verbose", "-v",
            help="Provides additional details for users",
            action="store_true",
            default=False,
            required=False,
        )
        parser.add_argument(
            "--jwt", help="JWT authentication token", default=None, required=False
        )
        parser.add_argument(
            "--user_key",
            help="Manually specify user key",
            default=False,
            required=False,
        )
        parser.add_argument(
            "--force_overwrite",
            help="Automatically overwrite any existing credentials stored in the config file for the specified user.",
            action="store_true",
            default=False,
            required=False,
        )
        parser.add_argument(
            "--gui",
            help="is use gui",
            default=False,
        )
    def filter_args(self, args):
        return {k: v for k, v in args.items() if k in edit_config.__code__.co_varnames}

    def perform_task(self, vars_args: dict):
        valid_args = self.filter_args(vars_args)
        return edit_config(**valid_args)
