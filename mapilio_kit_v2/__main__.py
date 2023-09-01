import argparse
from . import VERSION
from mapilio_kit_v2.base import Upload, Decompose, Authenticate


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

    # process
    parser_decompose = subparsers.add_parser("decompose", help="decompose help")
    parser_decompose.set_defaults(func=Decompose.run)

    # update
    parser_upload= subparsers.add_parser("upload", help="update help")
    parser_upload.set_defaults(func=Upload.run)


    #TODO move to upload class
    # Add --upgrade option
    parser_upload.add_argument("--processed", action="store_true", help="processed option")

    # authenticate
    parser_authenticate = subparsers.add_parser("authenticate", help="authenticate help")
    parser_authenticate.set_defaults(func=Authenticate.run)

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
