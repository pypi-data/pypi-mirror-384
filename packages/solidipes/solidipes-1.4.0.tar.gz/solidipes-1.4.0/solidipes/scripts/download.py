import argparse


command = "download"
command_help = "Download dataset to an online repository"


def main(args) -> None:
    from solidipes.utils.utils import get_key_to_parsables

    from solidipes.downloaders.downloader import Downloader

    key_to_downloaders = get_key_to_parsables("downloaders", Downloader)

    platform = args.platform
    downloader = key_to_downloaders[platform](**vars(args))
    downloader.download()


def populate_parser(parser) -> None:
    # Create subparsers for each download platform
    from solidipes.utils.utils import get_key_to_parsables
    from solidipes.downloaders.downloader import Downloader

    downloader_parsers = parser.add_subparsers(dest="platform", help="Target hosting platform")
    downloader_parsers.required = True

    key_to_downloaders = get_key_to_parsables("downloaders", Downloader)
    parsers = {}
    for key, downloader in key_to_downloaders.items():
        parsers[key] = downloader_parsers.add_parser(key, help=downloader.__doc__)
        downloader.populate_parser(parsers[key])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
