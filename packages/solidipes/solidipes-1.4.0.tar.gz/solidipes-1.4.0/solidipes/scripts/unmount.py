import argparse

command = "unmount"
command_help = "Unmount cloud storage"


def main(args) -> None:
    import os

    from ..mounters.cloud import list_mounts
    from ..utils import bcolors

    mounts = list_mounts(only_mounted=not args.forget)
    # --list-mounted: show mounted directories
    if args.list_mounted:
        print("Currently mounted directories:")

        for path, mount_info in mounts.items():
            if not mount_info.get("mounted"):
                continue
            print(f"    {path} {bcolors.BRIGHT_GREEN}({mount_info['type']}, {mount_info['system']}){bcolors.RESET}")

        return

    if args.all:
        from ..mounters.cloud import unmount_all

        unmount_all(**vars(args))
        return

    # --path: unmount specified directory, otherwise unmount all
    if args.path:
        path = args.path.rstrip(os.sep)
        if path not in mounts:
            print(f'"{path}" has not been mounted with "solidipes mount".')
            return
        paths_to_unmount = [path]
    else:
        paths_to_unmount = list(mounts.keys())

    if len(paths_to_unmount) == 0:
        print("Nothing to unmount.")
        return

    from solidipes.mounters.cloud import unmount

    for path in paths_to_unmount:  # path relative working directory
        try:
            args.path = path
            unmount(**vars(args))

        except RuntimeError as e:
            print(f"Error unmounting {path}: {e}")
            continue


def populate_parser(parser) -> None:
    parser.description = command_help

    parser.add_argument("path", help="Path of the directory to unmount.", nargs="?")

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Unmount all mounts",
    )

    parser.add_argument(
        "-f",
        "--forget",
        help="Also delete mount info from saved configuration",
        action="store_true",
    )

    parser.add_argument(
        "-l",
        "--list-mounted",
        help="List currently mounted directories",
        action="store_true",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
