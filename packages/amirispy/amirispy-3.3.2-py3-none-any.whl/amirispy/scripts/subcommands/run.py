# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts the command to run AMIRIS."""

import os
from pathlib import Path

from amirispy.source.cli import RunOptions
from amirispy.source.exception import AMIRISError
from amirispy.source.fameio_calls import compile_output, call_amiris, compile_input, determine_all_paths
from amirispy.source.files import ensure_folder_accessible
from amirispy.source.java import check_java
from amirispy.source.logs import log_error

_ERR_NOT_A_FILE = "Specified path '{}' is no file."


def run_amiris(options: dict) -> None:
    """Compiles a scenario, then runs AMIRIS, and finally extracts results.

    Compiles scenario to protobuf using fameio.scripts.make_config,
    executes AMIRIS, and extracts results using fameio.scripts.convert_results

    Args:
        options: dictionary of command line instructions

    Raises:
        AMIRISError: if any error occurred during execution of AMIRIS; logged with level "ERROR"
    """
    check_java(skip=options[RunOptions.NO_CHECKS])
    path_to_scenario: Path = options[RunOptions.SCENARIO]
    if not path_to_scenario.is_file():
        raise log_error(AMIRISError(_ERR_NOT_A_FILE.format(path_to_scenario)))
    original_wd = Path.cwd()

    paths = determine_all_paths(path_to_scenario, original_wd, options)
    ensure_folder_accessible(paths["RESULT_FOLDER"])

    os.chdir(paths["SCENARIO_DIRECTORY"])
    compile_input(options, paths)
    os.chdir(paths["RESULT_FOLDER"])
    call_amiris(paths)
    compile_output(options, paths)
    os.remove(paths["INPUT_PB"])
    os.chdir(original_wd)
