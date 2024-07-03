# -*- coding: utf-8 -*-
import sys
import os
import sentry_sdk
import requests
from colorama import Fore
import argparse

project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(project_root, 'components'))

from mapilio_kit.components.version import VERSION
from mapilio_kit.base import uploader, decomposer, authenticator, video_loader, image_and_csv_uploader, CSVprocessor, gopro360max_processor, Zipper, run_mapi
from mapilio_kit.components import arguments
from mapilio_kit.components.login import list_all_users
from mapilio_kit.components.config import delete_user

sentry_sdk.init(
    dsn="https://e64e5a7900578f279015f1c573318337@o4506428096577536.ingest.us.sentry.io/4507385354387456",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

def get_latest_version():
    url = "https://raw.githubusercontent.com/mapilio/mapilio-kit/main/mapilio_kit/components/version.py"
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        version_line = [line for line in content.split('\n') if 'VERSION' in line][0]
        latest_version = version_line.split('"')[1]
        return latest_version
    return None



FUNCTION_MAP = {'Upload': uploader,
                'Decompose': decomposer,
                'Authenticate': authenticator,
                'VideoUpload': video_loader,
                "image_and_csv_upload": image_and_csv_uploader,
                "CSVprocessor": CSVprocessor,
                "gopro360max_processor": gopro360max_processor,
                "Zipper": Zipper,
                "Run": run_mapi}


def get_parser(subparsers, funtion_map):
    for key, value in funtion_map.items():
        cmd_parser = subparsers.add_parser(
            value.name, help=value.help, conflict_handler="resolve")
        arguments.general_arguments(cmd_parser, value.name)
        value().fundamental_arguments(cmd_parser)
        cmd_parser.set_defaults(func=value().perform_task)

def del_useless_users():
       deleted_users= [delete_user(user_info['SettingsUsername']) for user_info in list_all_users() if 'SettingsEmail' not in user_info]
       if len(deleted_users):
           print(f"{Fore.RED}Useless account or accounts found and deleted! \n {Fore.RESET}")

def main():
    print(f"{Fore.BLUE}Welcome to Mapilio-kit\n"
         f"Mapilio allows you to upload your images, videos and 360 degree panorama images to Mapilio map.{Fore.RESET}\n")

    latest_version = get_latest_version()

    if latest_version:
        if latest_version > VERSION:
            print(f"{Fore.RED}A newer version ({latest_version}) is available!{Fore.RESET}")
            print(f'{Fore.RED}For latest Mapilio-kit version please update with "pip install mapilio_kit --upgrade"{Fore.RESET} \n')
        else:
            print(f"{Fore.GREEN}You have the latest Mapilio-kit version ({VERSION}) installed.{Fore.RESET}\n")
    else:
        print(f"{Fore.RED}Unable to fetch the latest Mapilio-kit version information.{Fore.RESET}\n")

    del_useless_users() # checks auth file and deletes users that are not included SettingsEmail

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
