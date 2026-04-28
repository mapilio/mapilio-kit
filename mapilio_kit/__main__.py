import argparse
import os
import sys

from colorama import Fore

project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(project_root, 'components'))

from mapilio_kit.base import (
    CSVprocessor,
    Zipper,
    authenticator,
    decomposer,
    doctor,
    gopro360max_processor,
    image_and_csv_uploader,
    run_mapi,
    sampler,
    uploader,
    validator,
    video_loader,
)
from mapilio_kit.components.auth.login import list_all_users
from mapilio_kit.components.utilities import arguments
from mapilio_kit.components.utilities.config import delete_user
from mapilio_kit.components.utilities.info import get_latest_version, maintenance_info
from mapilio_kit.components.version import VERSION


def _init_sentry() -> None:
    """Initialize Sentry only if a DSN is provided and telemetry is not disabled.

    Configuration is fully driven by environment variables so secrets are never
    committed to the repository:

      MAPILIO_KIT_SENTRY_DSN           - Sentry DSN (required to enable Sentry)
      MAPILIO_KIT_DISABLE_TELEMETRY    - Set to "1"/"true" to disable Sentry
      MAPILIO_KIT_SENTRY_TRACES_RATE   - Float [0.0, 1.0], default 0.1
      MAPILIO_KIT_SENTRY_PROFILES_RATE - Float [0.0, 1.0], default 0.1
    """
    disabled = os.environ.get("MAPILIO_KIT_DISABLE_TELEMETRY", "").lower() in {
        "1", "true", "yes", "on",
    }
    dsn = os.environ.get("MAPILIO_KIT_SENTRY_DSN", "").strip()
    if disabled or not dsn:
        return

    try:
        import sentry_sdk  # imported lazily so the package is optional at runtime
    except ImportError:
        return

    def _rate(name: str, default: float) -> float:
        try:
            return max(0.0, min(1.0, float(os.environ.get(name, default))))
        except (TypeError, ValueError):
            return default

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=_rate("MAPILIO_KIT_SENTRY_TRACES_RATE", 0.1),
        profiles_sample_rate=_rate("MAPILIO_KIT_SENTRY_PROFILES_RATE", 0.1),
        release=f"mapilio-kit@{VERSION}",
    )


_init_sentry()

FUNCTION_MAP = {'Upload': uploader,
                'Decompose': decomposer,
                'Authenticate': authenticator,
                'VideoUpload': video_loader,
                "image_and_csv_upload": image_and_csv_uploader,
                "CSVprocessor": CSVprocessor,
                "gopro360max_processor": gopro360max_processor,
                "Zipper": Zipper,
                "sampler": sampler,
                "Run": run_mapi,
                "Doctor": doctor,
                "Validate": validator}


def get_parser(subparsers, funtion_map):
    for key, value in funtion_map.items():
        cmd_parser = subparsers.add_parser(
            value.name, help=value.help, conflict_handler="resolve")
        arguments.general_arguments(cmd_parser, value.name)
        value().fundamental_arguments(cmd_parser)
        cmd_parser.set_defaults(func=value().perform_task)


def del_useless_users():
    deleted_users = [delete_user(user_info['SettingsUsername']) for user_info in list_all_users() if
                     'SettingsEmail' not in user_info]
    if len(deleted_users):
        print(f"{Fore.RED}Useless account or accounts found and deleted! \n {Fore.RESET}")


def main():
    print(f"{Fore.BLUE}Welcome to Mapilio-kit\n"
          f"Mapilio allows you to upload your images, videos and 360 degree panorama images to Mapilio map.{Fore.RESET}\n")

    latest_version = get_latest_version()
    maintenance_info()

    if latest_version:
        if latest_version > VERSION:
            print(f"{Fore.RED}A newer version ({latest_version}) is available!{Fore.RESET}")
            print(
                f'{Fore.RED}For latest Mapilio-kit version please update with "pip install mapilio_kit --upgrade"{Fore.RESET} \n')
        else:
            print(f"{Fore.GREEN}You have the latest Mapilio-kit version ({VERSION}) installed.{Fore.RESET}\n")
    else:
        print(f"{Fore.RED}Unable to fetch the latest Mapilio-kit version information.{Fore.RESET}\n")

    del_useless_users()  # checks auth file and deletes users that are not included SettingsEmail

    parser = argparse.ArgumentParser(description="mapi-kit-v2")

    parser.add_argument(
        "--version",
        help="shows the version of Mapilio",
        action="version",
        version=VERSION,
    )

    # Create subparsers for each command
    subparsers = parser.add_subparsers(dest="map", help="Available commands")

    get_parser(subparsers, FUNCTION_MAP)

    args = parser.parse_args()

    # Call the appropriate function based on the selected command
    if hasattr(args, 'func'):
        try:
            args.func(vars(args))
        except Exception as e:
            parser.error(e)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
