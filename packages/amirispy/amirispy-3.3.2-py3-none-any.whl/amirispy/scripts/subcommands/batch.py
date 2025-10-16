# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts the command to batch-run AMIRIS."""

import logging as log
import os
from pathlib import Path
from typing import List

from fameio.input import InputError
from fameio.input.loader import load_yaml
from fameio.input.scenario import Scenario
from fameio.input.validator import SchemaValidator
from fameio.logs import fameio_logger, LogLevel

from amirispy.scripts.subcommands.run import run_amiris
from amirispy.source.cli import BatchOptions, RunOptions
from amirispy.source.exception import AMIRISError
from amirispy.source.files import ensure_absolute
from amirispy.source.java import check_java
from amirispy.source.logs import log_and_print, log_error

_ERR_ALL_PATHS_INVALID = "Provided scenario path(s) '{}' contain no valid scenario YAML files."
_ERR_ABS_PATTERN = "Provided pattern '{}' must not start with a '/'."
_WARN_PATH_NOT_EXISTING = "Provided path '{}' is ignored as it is neither a file nor a directory."
_WARN_NO_VALID_FAME_SCENARIO = "'{}' is not a valid scenario file. You may improve the file name pattern using `-p`"
_PRINT_RUN = "AMIRIS run {} of {}: Simulate file '{}', find results at '{}'"


def batch_run_amiris(options: dict) -> None:
    """Compile, run, and extract multiple scenarios.

    Compile multiple scenarios to protobuf using fameio.scripts.make_config, execute AMIRIS,
    and extract results using fameio.scripts.convert_results.

    Args:
        options: dictionary of command line instructions

    Raises:
        AMIRISError: if any error occurs; logged with level "ERROR"
    """
    check_java(skip=options[BatchOptions.NO_CHECKS])
    input_yaml_files = find_valid_scenarios(
        options[BatchOptions.SCENARIOS], options[BatchOptions.RECURSIVE], options[BatchOptions.PATTERN]
    )
    run_options = options.copy()
    run_options.update(
        {
            RunOptions.JAR: options[BatchOptions.JAR],
            RunOptions.NO_CHECKS: True,
            RunOptions.OUTPUT_OPTIONS: options[BatchOptions.OUTPUT_OPTIONS],
        }
    )

    for i, input_yaml_file in enumerate(input_yaml_files):
        output_folder = ensure_absolute(options[BatchOptions.OUTPUT].joinpath(str(i)), Path.cwd())
        log_and_print(_PRINT_RUN.format(i + 1, len(input_yaml_files), input_yaml_file, output_folder))
        run_options.update({RunOptions.SCENARIO: input_yaml_file, RunOptions.OUTPUT: output_folder})
        run_amiris(run_options)


def find_valid_scenarios(search_paths: List[Path], recursive: bool, pattern: str) -> List[Path]:
    """Searches for valid scenario YAML files in given `input_yaml_paths`.

    Args:
        search_paths: path(s) which are to be searched for valid scenario files
        recursive: if true, subdirectories of each search path are searched as well
        pattern: that file names must match to be returned

    Returns:
        List of Paths to valid scenario files

    Raises:
        AMIRISError: if none of the files in path are a valid scenario or pattern is invalid; logged with level "ERROR"
    """
    files_to_test = get_inner_yaml_files(search_paths, recursive, pattern)
    fameio_logger(LogLevel.PRINT.name)
    scenario_files = [file for file in files_to_test if is_valid_fame_input_yaml(file)]
    if not scenario_files:
        raise log_error(AMIRISError(_ERR_ALL_PATHS_INVALID.format(search_paths)))
    log.info(f"Found these scenario file(s) '{scenario_files}'.")
    return scenario_files


def get_inner_yaml_files(paths: List[Path], recursive: bool, pattern: str) -> List[Path]:
    """Returns a list of all YAML files in `paths` (and all subdirectories when `recursive` is set to True).

    Args:
        paths: to search for YAML files
        recursive: if True, subdirectories are also searched
        pattern: that file names must match to be returned

    Returns:
        List of Paths to YAML files contained in `paths` (and its subdirectories)

    Raises:
        AMIRISError: if pattern is invalid; logged with level "ERROR"
    """
    yaml_files = []
    for path in paths:
        if path.is_file():
            yaml_files.append(path)
        elif path.is_dir():
            try:
                yaml_files.extend([f for f in path.glob(pattern) if f.is_file()])
            except NotImplementedError as e:
                raise log_error(AMIRISError(_ERR_ABS_PATTERN.format(pattern))) from e
            if recursive:
                yaml_files.extend(get_inner_yaml_files([f for f in path.glob("*") if f.is_dir()], recursive, pattern))
        else:
            log.warning(_WARN_PATH_NOT_EXISTING.format(path))
    return yaml_files


def is_valid_fame_input_yaml(file_to_test: Path) -> bool:
    """Checks if the given path points to a valid FAME input YAML file. If not, an error is logged.

    Args:
        file_to_test: Path to a file

    Returns:
        True if the given path points to valid FAME input YAML file, otherwise False
    """
    file_path = ensure_absolute(file_to_test, Path.cwd())
    original_cwd = Path.cwd()
    try:
        os.chdir(file_path.parents[0])
        scenario = Scenario.from_dict(load_yaml(file_path))
        SchemaValidator.validate_scenario_and_timeseries(scenario)
        return True
    except InputError as e:
        log.warning(_WARN_NO_VALID_FAME_SCENARIO.format(file_to_test))
        log.info(f"Error: {e}")
    finally:
        os.chdir(original_cwd)
    return False
