# PYTHON_ARGCOMPLETE_OK
import argparse

import argcomplete

from solidipes import __version__
from solidipes.scripts import (
    download,
    generate_report,
    init,
    install_completion,
    mount,
    quick_view,
    shell,
    unmount,
    upload,
)
from solidipes.utils.utils import get_solidipes_directory

commands = [
    download,
    generate_report,
    init,
    install_completion,
    mount,
    quick_view,
    shell,
    unmount,
    upload,
]


def main_PYTHON_ARGCOMPLETE_OK() -> None:
    """Entry point for the command line interface."""
    args = parse_args()

    if args.init:

        class InitArgs:
            directory = "."
            force = False

        init_args = InitArgs()
        init.main(init_args)

        if args.command == "init":
            return

    if args.command not in ["download", "init", "install-completion", "shell"]:
        try:
            get_solidipes_directory()
        except FileNotFoundError:
            print(
                'Please run "solidipes init" at the root directory of your study before running other Solidipes'
                " commands."
            )
            return

    try:
        for command in commands:
            if args.command == command.command:
                command.main(args)
                break
    except Exception as e:
        if args.verbose:
            raise e
        print(f"FATAL: {e}")
        import sys

        sys.exit(-1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.prog = "solidipes"

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the current version of the Solidipes",
    )

    parser.add_argument("--verbose", action="store_true")

    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize a Solidipes study at the current directory if necessary",
    )

    # Create subparsers for each command
    command_parsers = parser.add_subparsers(dest="command", help="command to run")
    command_parsers.required = True

    for command in commands:
        command_parser = command_parsers.add_parser(command.command, help=command.command_help)
        command.populate_parser(command_parser)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main_PYTHON_ARGCOMPLETE_OK()
