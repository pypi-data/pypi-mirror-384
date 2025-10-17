import argparse

command = "view"
command_help = "Generate a view from a file"

################################################################


def main(args) -> None:
    """Generate a .py report for the given directory."""
    from ..loaders.file import load_file
    from ..loaders.sequence import Sequence
    from ..viewers import backends as viewer_backends

    path = args.path
    _file = load_file(path)
    print(f"Reading {path}: {_file}")

    if viewer_backends.current_backend == "streamlit":
        import streamlit as st

        st.set_page_config(layout="wide")

    if args.item > 0 and isinstance(_file, Sequence):
        _file.select_element(args.item)
    _file.view()


def populate_parser(parser) -> None:
    parser.description = """Generate view for the given file."""

    parser.add_argument("path", help="Path to file to be viewed")
    parser.add_argument(
        "--item",
        type=int,
        default=0,
        help="In case the object is a sequence helpful to select the correct item",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
