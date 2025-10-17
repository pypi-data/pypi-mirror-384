import argparse

from ..utils import solidipes_logging as logging

command = "mount"
command_help = "Mount cloud storage"
logger = logging.getLogger()

################################################################


def main(args) -> None:
    from ..mounters.cloud import list_mounts, mount_all
    from ..utils import bcolors

    # --all: mount all existing mount points
    if args.all:
        mount_all(**vars(args))
        return

    # --list-existing: show existing mount points
    if args.list_existing:
        mounts = list_mounts()
        print("Existing mount points:")

        for path, mount_info in mounts.items():
            mounted_message = " mounted" if mount_info["mounted"] else ""
            print(f"    {path} {bcolors.BRIGHT_GREEN}{mount_info['type']} {mounted_message}{bcolors.RESET}")

        if not mounts:
            print(f"    {bcolors.RED}No mount point found{bcolors.RESET}")
        return
    from solidipes.mounters.cloud import mount

    if args.convert:
        raise RuntimeError("conversion feature currently disabled")

    for f in ["command", "list_existing", "convert", "all"]:
        if hasattr(args, f):
            del args.__dict__[f]

    from solidipes.utils.utils import ExecError

    try:
        if not hasattr(args, "path"):
            global current_parser
            if current_parser is None:
                logger.error("No path provided")
                return
            current_parser.print_help()
        else:
            mount(**vars(args))
    except ExecError as e:
        logger.error(e)


################################################################

current_parser = None


def populate_parser(parser) -> None:
    global current_parser
    current_parser = parser
    parser.description = command_help
    from solidipes.utils.utils import get_key_to_parsables
    from solidipes.mounters.cloud import Mounter

    main_options = parser.add_mutually_exclusive_group(required=False)
    main_options.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Mount all existing mounting points (not already mounted).",
    )

    main_options.add_argument(
        "-l",
        "--list-existing",
        action="store_true",
        help="List existing mount points.",
    )

    main_options.add_argument(
        "-c",
        "--convert",
        action="store_true",
        help=(
            "Send the contents of the local directory to the cloud"
            " storage (convert it to cloud storage). (BROKEN"
            " currently)"
        ),
    )

    # Cloud types subparsers
    mount_parsers = parser.add_subparsers(dest="type", help="Type of cloud storage to mount")
    key_to_mounter = get_key_to_parsables("mounters", Mounter)
    parsers = {}
    for key, mounter in key_to_mounter.items():
        parsers[key] = mount_parsers.add_parser(key, help=mounter.__doc__)
        mounter.populate_parser(parsers[key])


################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
