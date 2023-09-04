import argparse
from . import VERSION
from .base import loader,decomposer,authenticator
from .components import arguments

FUNCTION_MAP = {'Upload' : loader,
                'Decompose' : decomposer ,
                'Authenticate' : authenticator,}

def get_parser(subparsers,funtion_map):
    for key, value in funtion_map.items():
        print(value, key)
        cmd_parser = subparsers.add_parser(
            value.name, help=value.help, conflict_handler="resolve")
        arguments.general_arguments(cmd_parser, value.name)
        value().fundamental_arguments(cmd_parser)
        cmd_parser.set_defaults(func=value().run)

def main():
    parser = argparse.ArgumentParser(description="mapi-kit-v2")

    parser.add_argument(
        "--version",
        help="shows the version of Mapilio",
        action="version",
        version=VERSION,
    )

    # Create subparsers for each command
    subparsers = parser.add_subparsers(dest="map", help="Available commands")

    get_parser(subparsers,FUNCTION_MAP)

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
