# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts command line parsing, its options and errors."""

import argparse
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, List

from amirispy.scripts.subcommands.download import DownloadMode
from amirispy.source.files import find_files
from amirispy.source.logs import LogLevels


class CommandLineError(Exception):
    """An error that occurred while parsing the command line options."""


AMIRIS_PARSER = "Command-line interface to the electricity market model AMIRIS"
AMIRIS_LOG_FILE_HELP = "Provide logging file (default: None)"
AMIRIS_LOG_LEVEL_HELP = f"Choose logging level (default: {LogLevels.ERROR.name})"
AMIRIS_COMMAND_HELP = "Choose one of the following commands:"

INSTALL_DEPRECATION = "'install' command is deprecated: use 'download' instead."
DOWNLOAD_HELP = "Downloads and extracts latest open access AMIRIS instance"
DOWNLOAD_URL_MODEL_HELP = "URL to download AMIRIS model from (default: latest AMIRIS artifact)"
DOWNLOAD_TARGET_HELP = "Folder to download 'amiris-core_<version>-jar-with-dependencies.jar' to (default: './')"
DOWNLOAD_FORCE_HELP = "Force download to overwrite existing AMIRIS and/or example files (default: False)"
DOWNLOAD_MODE_HELP = "Choose to download model and examples `all` (default), or `model` / `examples` only"

RUN_HELP = "Compile scenario, execute AMIRIS, and extract results"
RUN_JAR_HELP = "Path to 'amiris-core_<version>-jar-with-dependencies.jar (default: 'amiris*.jar' in current directory)"
RUN_JAR_DEFAULT = "amiris*.jar"
RUN_JAR_ERR_MISSING = "No jar-file found with pattern: '{}'"
RUN_JAR_ERR_TOO_MANY = "More than one jar-file found with pattern: '{}'"
RUN_SCENARIO_HELP = "Path to a scenario yaml-file"
RUN_OUTPUT_HELP = "Directory to write output to"
RUN_OUTPUT_OPTION_HELP = (
    "optional pass through of FAME-Io's output conversion options, see "
    "https://gitlab.com/fame-framework/fame-io/-/blob/main/README.md#read-fame-results"
)
RUN_NO_CHECK_HELP = "Skip checks for Java installation and correct version"

BATCH_HELP = "Batch mode to perform multiple runs each with scenario compilation, execution, and results extraction"
BATCH_SCENARIO_HELP = "Path to single or list of: scenario yaml-files or their enclosing directories"
BATCH_RECURSIVE_HELP = "Option to recursively search in provided Path for scenario (default: False)"
DEFAULT_PATTERN = "*.y*ml"
BATCH_PATTERN_HELP = f"Optional name pattern that scenario files searched for must match (default: '{DEFAULT_PATTERN}')"

COMPARE_HELP = "Compare if results of two AMIRIS runs and equivalent"
COMPARE_EXPECTED_HELP = "Path to folder with expected results"
COMPARE_TEST_HELP = "Path to folder with results to test"
COMPARE_IGNORE_HELP = "Optional list of file names to not be compared"
URL_LATEST_AMIRIS = "https://gitlab.com/dlr-ve/esy/amiris/amiris/-/jobs/artifacts/main/download?job=deploy:jdk11"


class GeneralOptions(Enum):
    """Specifies general options for workflow."""

    LOG = auto()
    LOGFILE = auto()


class Command(Enum):
    """Specifies command to execute."""

    RUN = auto()
    DOWNLOAD = auto()
    COMPARE = auto()
    BATCH = auto()


class CompareOptions(Enum):
    """Options for command `compare`."""

    EXPECTED = auto()
    TEST = auto()
    IGNORE = auto()


class DownloadOptions(Enum):
    """Options for command `download`."""

    URL = auto()
    TARGET = auto()
    FORCE = auto()
    MODE = auto()


class RunOptions(Enum):
    """Options for command `run`."""

    JAR = auto()
    SCENARIO = auto()
    OUTPUT = auto()
    OUTPUT_OPTIONS = auto()
    NO_CHECKS = auto()


class BatchOptions(Enum):
    """Options for command `batch`."""

    JAR = auto()
    SCENARIOS = auto()
    OUTPUT = auto()
    OUTPUT_OPTIONS = auto()
    NO_CHECKS = auto()
    RECURSIVE = auto()
    PATTERN = auto()


Options = {
    Command.COMPARE: CompareOptions,
    Command.RUN: RunOptions,
    Command.DOWNLOAD: DownloadOptions,
    Command.BATCH: BatchOptions,
}


def arg_handling_run(input_args: Optional[List[str]] = None) -> Tuple[Command, Dict[Enum, Any]]:
    """Handles command line arguments for `amiris` and returns `command` and its options `args`.

    Allows to set args from a list of input_args.

    Raises:
        CommandLineError: if a custom error occurred during command-line handling
    """

    parent_parser = argparse.ArgumentParser(prog="amiris", description=AMIRIS_PARSER)
    parent_parser.add_argument("-lf", "--logfile", type=Path, required=False, help=AMIRIS_LOG_FILE_HELP)
    parent_parser.add_argument(
        "-l",
        "--log",
        default=LogLevels.WARN.name,
        choices=[level.name.lower() for level in LogLevels],
        help=AMIRIS_LOG_LEVEL_HELP,
    )
    subparsers = parent_parser.add_subparsers(dest="command", required=True, help=AMIRIS_COMMAND_HELP)

    download_parser = subparsers.add_parser("download", help=DOWNLOAD_HELP)
    add_download_arguments(download_parser)

    install_parser = subparsers.add_parser("install", help=INSTALL_DEPRECATION)
    add_download_arguments(install_parser)

    run_parser = subparsers.add_parser("run", help=RUN_HELP)
    run_parser.add_argument("--scenario", "-s", type=Path, required=True, help=RUN_SCENARIO_HELP)
    run_parser.add_argument("--jar", "-j", type=str, default=RUN_JAR_DEFAULT, help=RUN_JAR_HELP)
    run_parser.add_argument("--output", "-o", type=Path, default=Path("./result"), help=RUN_OUTPUT_HELP)
    run_parser.add_argument("--output-options", "-oo", type=str, default="", help=RUN_OUTPUT_OPTION_HELP)
    run_parser.add_argument("--no-checks", "-nc", action="store_true", default=False, help=RUN_NO_CHECK_HELP)

    batch_parser = subparsers.add_parser("batch", help=BATCH_HELP)
    batch_parser.add_argument("--scenarios", "-s", nargs="+", type=Path, required=True, help=BATCH_SCENARIO_HELP)
    batch_parser.add_argument("--jar", "-j", type=str, default=RUN_JAR_DEFAULT, help=RUN_JAR_HELP)
    batch_parser.add_argument("--output", "-o", type=Path, default=Path("./result"), help=RUN_OUTPUT_HELP)
    batch_parser.add_argument("--recursive", "-r", default=False, action="store_true", help=BATCH_RECURSIVE_HELP)
    batch_parser.add_argument("--pattern", "-p", type=str, default=DEFAULT_PATTERN, help=BATCH_PATTERN_HELP)
    batch_parser.add_argument("--output-options", "-oo", type=str, default="", help=RUN_OUTPUT_OPTION_HELP)
    batch_parser.add_argument("--no-checks", "-nc", action="store_true", default=False, help=RUN_NO_CHECK_HELP)

    compare_parser = subparsers.add_parser("compare", help=COMPARE_HELP)
    compare_parser.add_argument("--expected", "-e", type=Path, required=True, help=COMPARE_EXPECTED_HELP)
    compare_parser.add_argument("--test", "-t", type=Path, required=True, help=COMPARE_TEST_HELP)
    compare_parser.add_argument("--ignore", "-i", required=False, help=COMPARE_IGNORE_HELP)

    args = vars(parent_parser.parse_args(input_args))
    command = get_command_from_string(args.pop("command"))
    if command in (Command.RUN, Command.BATCH):
        args["jar"] = find_single_executable_path(args["jar"])
    return command, enumify(command, args)


def add_download_arguments(parser: argparse.ArgumentParser) -> None:
    """Adds download arguments to given parser."""
    parser.add_argument("--url", "-u", default=URL_LATEST_AMIRIS, help=DOWNLOAD_URL_MODEL_HELP)
    parser.add_argument("--target", "-t", type=Path, default=Path("./"), help=DOWNLOAD_TARGET_HELP)
    parser.add_argument("--force", "-f", default=False, action="store_true", help=DOWNLOAD_FORCE_HELP)
    parser.add_argument(
        "--mode",
        "-m",
        type=str.lower,  # noqa
        choices=[mode.name.lower() for mode in DownloadMode],
        default=DownloadMode.ALL.name,
        help=DOWNLOAD_MODE_HELP,
    )


def get_command_from_string(command_str: str) -> Command:
    """Returns Command extracted from given string."""
    if command_str == "install":
        print(INSTALL_DEPRECATION)
        command_str = "download"
    return Command[command_str.upper()]


def find_single_executable_path(pattern: str) -> Path:
    """Searches for single file with given `pattern`; Raises an error if no file or more than one file match."""
    matching_files = find_files(pattern)
    if len(matching_files) == 0:
        raise CommandLineError(RUN_JAR_ERR_MISSING.format(pattern))
    if len(matching_files) > 1:
        raise CommandLineError(RUN_JAR_ERR_TOO_MANY.format(pattern))
    return Path(matching_files[0])


def enumify(command: Command, args: dict) -> Dict[Enum, Any]:
    """Matches `args` for given `command` to their respective Enum."""

    result = {}
    for option in GeneralOptions:
        result[option] = args.pop(option.name.lower())

    for option in Options[command]:
        result[option] = args.pop(option.name.lower())
    return result
