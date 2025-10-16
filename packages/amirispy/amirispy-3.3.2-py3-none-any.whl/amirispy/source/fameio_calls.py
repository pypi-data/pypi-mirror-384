# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts methods to call FAME-Io."""

import logging as log
import subprocess
from pathlib import Path
from typing import Dict

from fameio.cli.convert_results import handle_args as handle_output_args
from fameio.cli.options import Options, ResolveOptions, TimeOptions
from fameio.scripts import ScriptError
from fameio.scripts.convert_results import run as convert_results
from fameio.scripts.make_config import run as make_config

from amirispy.source.cli import GeneralOptions, RunOptions
from amirispy.source.exception import AMIRISError
from amirispy.source.files import ensure_absolute
from amirispy.source.logs import log_error

ERR_FAMEIO_OUTPUT_ARGS = "Invalid fameio output conversion options: '{}'"
ERR_COMPILE = "Error during input file compilation in FAME-Io from scenario `{}`"
ERR_RUN = "Error during AMIRIS model run. Call was '{}'"
ERR_CONVERT = "Error during converting output file in FAME-Io"
INFO_START_COMPILE = "Creating binary protobuf input file: `{}` from scenario `{}`"


def determine_all_paths(scenario_yaml: Path, working_directory: Path, options: Dict) -> Dict[str, Path]:
    """Determines all Paths for the given scenario file and working directory.

    Args:
        scenario_yaml: path to the scenario file
        working_directory: the base working directory
        options: amiris-py command line options for the `run` command

    Returns:
        Dictionary containing all Paths to final results and temporary files
    """
    result_folder = ensure_absolute(options[RunOptions.OUTPUT], working_directory)
    jar_file = ensure_absolute(Path(options[RunOptions.JAR]), working_directory)
    return {
        "SCENARIO_FILE": ensure_absolute(scenario_yaml, working_directory),
        "SCENARIO_DIRECTORY": scenario_yaml.parent,
        "BASE_NAME": scenario_yaml.stem,
        "JAR_FILE": jar_file,
        "SETUP_FILE": jar_file.parents[0].joinpath("fameSetup.yaml"),
        "RESULT_FOLDER": result_folder,
        "INPUT_PB": result_folder.joinpath("input.pb"),
        "OUTPUT_PB": result_folder.joinpath("output.pb"),
    }


def compile_input(options: dict, paths: Dict[str, Path]) -> None:
    """Creates protobuf file using given `options` and `paths`.

    Args:
        options: for logging
        paths: to given input and output files

    Raises:
        AMIRISError: if input protobuf fails to compile; logged with level "ERROR"
    """
    fameio_input_config = {
        Options.FILE: paths["SCENARIO_FILE"].resolve(),
        Options.LOG_LEVEL: options[GeneralOptions.LOG],
        Options.LOG_FILE: options[GeneralOptions.LOGFILE],
        Options.OUTPUT: paths["INPUT_PB"],
    }
    log.info(INFO_START_COMPILE.format(fameio_input_config[Options.OUTPUT], fameio_input_config[Options.FILE]))
    try:
        make_config(fameio_input_config)
    except ScriptError:
        raise log_error(AMIRISError(ERR_COMPILE.format(fameio_input_config[Options.FILE])))


def call_amiris(paths: Dict[str, Path]) -> None:
    """Run AMIRIS using given paths.

    Args:
        paths: to all required files

    Raises:
        AMIRISError: if any error occurred during AMIRIS model run; logged with level "ERROR"
    """
    call = 'java -jar "{}" -f "{}" -o "output.pb"'.format(paths["JAR_FILE"], paths["INPUT_PB"])
    log.info(f"Calling AMIRIS with {paths['SCENARIO_FILE']}")
    try:
        subprocess.run(call, shell=True, check=True)
    except subprocess.SubprocessError:
        raise log_error(AMIRISError(ERR_RUN.format(call)))


def compile_output(options: Dict, paths: Dict[str, Path]) -> None:
    """Conducts to conversion of AMIRIS output to CSV files based on given options and paths.

    Args:
        options: for logging
        paths: to given input and output files

    Raises:
        AMIRISError: if an error occurred during output file conversion; logged with level "ERROR"
    """
    default_fameio_output_config = {
        Options.FILE: paths["OUTPUT_PB"].resolve(),
        Options.LOG_LEVEL: options[GeneralOptions.LOG],
        Options.LOG_FILE: options[GeneralOptions.LOGFILE],
        Options.AGENT_LIST: None,
        Options.OUTPUT: ".",
        Options.SINGLE_AGENT_EXPORT: False,
        Options.MEMORY_SAVING: False,
        Options.RESOLVE_COMPLEX_FIELD: ResolveOptions.SPLIT.name,
        Options.TIME: TimeOptions.UTC.name,
        Options.TIME_MERGING: [0, 1800, 1799],
    }
    log.info("Converting protobuf to csv files")
    fameio_output_config = override_eligible_defaults(default_fameio_output_config, options[RunOptions.OUTPUT_OPTIONS])
    try:
        convert_results(fameio_output_config)
    except ScriptError:
        raise log_error(AMIRISError(ERR_CONVERT))


def override_eligible_defaults(defaults: Dict, overrides: str) -> Dict:
    """Replaces default fameio arguments with given overrides; ensures that the output folder and file are not modified.

    Args:
        defaults: standard fameio output options
        overrides: (possibly empty) list of fameio output arguments to be used instead

    Returns:
        dict of (modified) fameio arguments

    Raises:
        AMIRISError: if invalid fameio output conversion options are received; logged with level "ERROR"
    """
    fixed_output_folder = defaults[Options.OUTPUT]
    fixed_file_to_convert = defaults[Options.FILE]
    try:
        argument_list = overrides.split()
        fameio_output_config = handle_output_args(argument_list, defaults)
    except SystemExit:
        raise log_error(AMIRISError(ERR_FAMEIO_OUTPUT_ARGS.format(overrides)))
    fameio_output_config[Options.OUTPUT] = fixed_output_folder
    fameio_output_config[Options.FILE] = fixed_file_to_convert
    return fameio_output_config
