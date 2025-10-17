import argparse


command = "upload"
command_help = "Upload dataset to an online repository"


def main(args) -> None:
    from solidipes.utils.utils import get_key_to_parsables
    from solidipes.uploaders.uploader import Uploader

    key_to_uploaders = get_key_to_parsables("uploaders", Uploader)
    platform = args.platform
    uploader = key_to_uploaders[platform](**vars(args))
    uploader.upload()


def populate_parser(parser) -> None:
    # Create subparsers for each upload platform
    from solidipes.utils.utils import get_key_to_parsables
    from solidipes.uploaders.uploader import Uploader

    uploader_parsers = parser.add_subparsers(dest="platform", help="Target hosting platform")
    uploader_parsers.required = True
    key_to_uploaders = get_key_to_parsables("uploaders", Uploader)
    parsers = {}
    for key, uploader in key_to_uploaders.items():
        parsers[key] = uploader_parsers.add_parser(key, help=uploader.__doc__)
        uploader.populate_parser(parsers[key])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
