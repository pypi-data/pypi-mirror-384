import argparse

from solidipes.plugins.discovery import report_list

# from solidipes.utils import mount_all

command = "report"
command_help = "Generate a report or launch a report interface for the given directory"


# Get all report makers
report_subclasses_instances = [Subclass() for Subclass in report_list]
reports = {command: report for report in report_subclasses_instances for command in [report.command, *report.aliases]}


def main(args) -> None:
    report_type = args.report_type
    report = reports[report_type]
    # mount_all(headless=True)
    report.make(args)


def populate_parser(parser) -> None:
    # Create subparsers for each report type
    report_parsers = parser.add_subparsers(dest="report_type", help="Type of report to generate")
    report_parsers.required = True

    for report in report_subclasses_instances:
        uploader_parser = report_parsers.add_parser(report.command, aliases=report.aliases, help=report.command_help)
        report.populate_parser(uploader_parser)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)
