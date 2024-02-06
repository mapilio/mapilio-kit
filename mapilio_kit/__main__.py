# -*- coding: utf-8 -*-
import sys
import os

project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(project_root, 'components'))

import argparse
from .components.version import VERSION
from .base import uploader, decomposer, authenticator, video_loader, image_and_csv_uploader, CSVprocessor, gopro360max_processor, Zipper, run_mapi
from .components import arguments
import requests
from colorama import Fore
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


def main():
    latest_version = get_latest_version()

    if latest_version:
        if latest_version > VERSION:
            print(f"{Fore.RED}A newer version ({latest_version}) is available!")
            print(f'{Fore.RED}For latest Mapilio-kit version please update with "pip install mapilio_kit --upgrade" \n')
        else:
            print(f"{Fore.GREEN}You have the latest Mapilio-kit version ({VERSION}) installed.\n")
    else:
        print(f"{Fore.RED}Unable to fetch the latest Mapilio-kit version information.\n")

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
