import argparse
from . import VERSION
from .base import loader,decomposer,authenticator

FUNCTION_MAP = {'Upload' : loader,
                'Decompose' : decomposer ,
                'Authenticate' : authenticator,}
                # 'Download' : Download }

def get_parser(subparsers,funtion_map):
    for key, value in funtion_map.items():
        print(value, key)
        cmd_parser = subparsers.add_parser(
            value.name, help=value.help, conflict_handler="resolve")
        value().add_basic_arguments(cmd_parser)
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
    # # decompose
    # parser_decompose = subparsers.add_parser("decompose", help="decompose help")
    # parser_decompose.set_defaults(func=decomposer.run)
    # cmd_parser = subparsers.add_parser(
    #                   decomposer.name, help=decomposer.help, conflict_handler="resolve")
    # decomposer.add_basic_arguments(cmd_parser)
    #
    # # upload
    # parser_upload= subparsers.add_parser("upload", help="update help")
    # parser_upload.set_defaults(func=loader.run)
    # cmd_parser = subparsers.add_parser(
    #     loader.name, help=loader.help, conflict_handler="resolve")
    # loader.add_basic_arguments(cmd_parser)
    #
    # # authenticate
    # parser_authenticate = subparsers.add_parser("authenticate", help="authenticate help")
    # cmd_parser = subparsers.add_parser(
    #     authenticator.name, help=authenticator.help, conflict_handler="resolve")
    # parser_authenticate.set_defaults(func=authenticator.run)
    # authenticator.add_basic_arguments(cmd_parser)

    args = parser.parse_args()
    
    # Call the appropriate function based on the selected command

    print(f"argparse vars: {vars(args)}")
    args.func(vars(args))

    if hasattr(args, 'func'):
        try:
            args.func(vars(args))
        except Exception as e:
            parser.error(e)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
