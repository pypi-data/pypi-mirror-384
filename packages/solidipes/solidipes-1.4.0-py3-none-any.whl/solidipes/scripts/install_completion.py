import argparse

command = "install-completion"
command_help = "Enable <Tab> auto-completion in the terminal"


def main(args) -> None:
    import os
    import sys
    import subprocess

    executable_path = os.path.join(os.path.dirname(sys.executable), "activate-global-python-argcomplete")
    command = [executable_path]

    if args.user:
        command.append("--user")

    if args.sudo:
        command = ["sudo"] + command

    ret = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ret.returncode == 0:
        print("Auto-completion enabled successfully.")
        return

    error_message = ret.stderr.decode()
    if "Please run this command using sudo" in error_message:
        print("Permission denied. Please run the command using the --user or --sudo option.")
    else:
        print(error_message.strip())


def populate_parser(parser) -> None:
    parser.description = command_help

    parser.add_argument(
        "-u",
        "--user",
        help="Install into user directory",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--sudo",
        help="Run with sudo",
        action="store_true",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
