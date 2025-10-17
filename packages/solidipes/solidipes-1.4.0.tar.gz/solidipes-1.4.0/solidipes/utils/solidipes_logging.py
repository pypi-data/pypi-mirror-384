#!/usr/bin/env python

import logging
import os
import sys

from .utils import bcolors, get_study_log_path
from typing import NoReturn

# Base level logger
root_logger = logging.getLogger("solidipes")
root_logger.propagate = True
root_logger.setLevel(logging.INFO)  # Avoid hard-filtering

# Logging format
if "FULL_SOLIDIPES_LOG" in os.environ:
    SOLIDIPES_FORMAT = (
        "%(prefix_color)s%(pathname)s:%(lineno)d:%(levelname)s:%(color_reset)s"
        " %(message_color)s%(message)s%(color_reset)s"
    )
else:
    SOLIDIPES_FORMAT = "%(prefix_color)s%(levelname)s:%(color_reset)s %(message_color)s%(message)s%(color_reset)s"


class FormatterShell(logging.Formatter):
    PREFIX_COLORS = {
        logging.DEBUG: bcolors.BRIGHT_BLUE,
        logging.INFO: bcolors.BRIGHT_BLACK,
        logging.WARNING: bcolors.BRIGHT_YELLOW,
        logging.ERROR: bcolors.BRIGHT_RED,
        logging.CRITICAL: bcolors.BOLD + bcolors.BRIGHT_RED,
    }

    MESSAGE_COLORS = {
        logging.DEBUG: bcolors.BRIGHT_BLUE,
        logging.INFO: bcolors.BRIGHT_BLACK,
        logging.WARNING: bcolors.BRIGHT_YELLOW,
        logging.ERROR: bcolors.BRIGHT_RED,
        logging.CRITICAL: bcolors.BOLD + bcolors.BRIGHT_RED,
    }

    def __init__(self, fmt) -> None:
        super().__init__(fmt)

    def format(self, record):
        record.prefix_color = self.PREFIX_COLORS[record.levelno]
        record.message_color = self.MESSAGE_COLORS[record.levelno]
        record.color_reset = bcolors.RESET
        return super().format(record)


formatter_sh = FormatterShell(SOLIDIPES_FORMAT)

SOLIDIPES_FORMAT = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s: %(message)s"
formatter_file = logging.Formatter(SOLIDIPES_FORMAT)


sh = logging.StreamHandler(sys.stderr)
if "FULL_SOLIDIPES_LOG" not in os.environ:
    sh.setLevel(logging.INFO)  # Only show info
    root_logger.setLevel(logging.INFO)
else:
    sh.setLevel(logging.DEBUG)
    root_logger.setLevel(logging.DEBUG)
sh.setFormatter(formatter_sh)
root_logger.addHandler(sh)

try:
    log_filename = get_study_log_path()
    file_handler = logging.FileHandler(log_filename, mode="a+")
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter_file)

    root_logger.addHandler(file_handler)
    root_logger.debug("Activated logging to file")

except FileNotFoundError:
    root_logger.debug("Cannot activate logging to file")

except PermissionError:
    root_logger.info("Cannot activate logging to file")


def getLogger():
    return logging.getLogger("solidipes")


def invalidPrint(x) -> NoReturn:
    raise Exception('print should not be used in that class: use the logging system instead: "{0}"'.format(x))
