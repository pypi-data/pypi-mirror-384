import argparse

command = "init"
command_help = "Initialize a study directory with Solidipes"


def main(args) -> None:
    import os

    from ..utils import get_study_root_path

    # Prevent initialization directly in user's home directory
    if os.path.abspath(args.directory) == os.path.expanduser("~"):
        print("You cannot initialize a Solidipes study in your home directory.")
        return

    # Prevent initialization of a study in a study
    if not args.force:
        try:
            root_directory = get_study_root_path(args.directory)

            # No exception: directory already exists, warn user and exit
            print(
                "The directory is already inside a Solidipes study directory,"
                f' whose root is "{root_directory}". Run the command with'
                ' "--force" to initialize anyway.'
            )
            return

        except FileNotFoundError:
            # No solidipes directory
            pass

    create_solidipes_directory(args.directory, args.force)
    create_metadata_file(args.directory)
    create_ignore_file(args.directory)


def create_solidipes_directory(root_directory, force=False):
    import os

    from ..utils import solidipes_dirname

    config_directory = os.path.join(root_directory, solidipes_dirname)

    # If the directory already exists, force remove it
    if force and os.path.isdir(config_directory):
        import shutil

        shutil.rmtree(config_directory)

    os.mkdir(config_directory)
    print(f'Created directory "{config_directory}"')

    return config_directory


def get_existing_description(root_directory):
    """Generate description field from existing README.md and DESCRIPTION.md files."""
    import os

    from ..utils import get_readme_path, get_study_description_path

    readme_path = get_readme_path(initial_path=root_directory)
    if os.path.isfile(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
    else:
        readme = ""

    description_path = get_study_description_path(initial_path=root_directory)
    if os.path.isfile(description_path):
        with open(description_path, "r", encoding="utf-8") as f:
            description = f.read()
    else:
        description = ""

    # Concatenate the content of both files
    if readme != "":
        if description != "":
            description = "\n\n" + description
        description = readme + description

    return description


def create_metadata_file(root_directory) -> None:
    """Create a metadata file with empty required fields."""
    from ..utils import get_study_metadata_path, set_study_metadata
    from ..utils import study_medatada_mandatory_fields as mandatory_fields

    config = mandatory_fields.copy()
    description = get_existing_description(root_directory)
    config["description"] = description

    # Write to file
    set_study_metadata(config, initial_path=root_directory)
    metadata_path = get_study_metadata_path(initial_path=root_directory)

    print(
        f"Metadata file {metadata_path} created. For publication to Zenodo,"
        " please consult https://developers.zenodo.org/#representation under"
        ' "Deposit metadata" for more information about the available and'
        " required fields."
    )


def create_ignore_file(root_directory) -> None:
    """Create default ignore file."""
    from ..utils import default_ignore_patterns, set_ignore

    set_ignore(default_ignore_patterns, initial_path=root_directory)


def populate_parser(parser) -> None:
    parser.description = command_help

    parser.add_argument(
        "directory",
        nargs="?",
        default="",
        help="Path to the directory to initialize. Defaults to the current directory. Cannot be your home directory.",
    )

    parser.add_argument(
        "-f",
        "--force",
        help=(
            "Force the creation of solidipes configuration files in the"
            " current directory. WARNING: This could erase an existing"
            " .solidipes directory!"
        ),
        action="store_true",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
