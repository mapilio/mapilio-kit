import argparse
import inspect



class Authenticate:
    name = "authenticate"
    help = "authenticate Mapilio users"

    def add_basic_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--config_file",
            help="Full path to the config file to be edited. Default is ~/.config/mapilio/configs/MLY_CLIENT_ID",
            default=None,
            required=False,
        )

        # The user_name, user_email, and user_password arguments are used to create
        # a Mapilio account. If all three are specified, a Mapilio account is created
        # and the user is logged in. If only the user_email is specified, the user
        # is logged in. If only the user_name is specified, the user is logged in
        # using the stored credentials.
        parser.add_argument(
            "--user_name",
            help="Mapilio user name",
            default=None,
            required=False,
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

        # The jwt argument is used to authenticate the user.
        parser.add_argument(
            "--jwt",
            help="JWT authentication token",
            default=None,
            required=False,
        )

        # The user_key argument is used to manually specify the user key.
        parser.add_argument(
            "--user_key",
            help="Manually specify user key",
            default=False,
            required=False,
        )

        # The force_overwrite argument is used to automatically overwrite any existing
        # credentials stored in the config file for the specified user.
        parser.add_argument(
            "--force_overwrite",
            help="Automatically overwrite any existing credentials stored in the config file for the specified user.",
            action="store_true",
            default=False,
            required=False,
        )

    def run(self, vars_args: dict):
        # Authenticate to the API using the provided credentials.
        authenticate(
            **(
                {
                    k: v
                    for k, v in vars_args.items()
                    if k in inspect.getfullargspec(authenticate).args
                }
            )
        )