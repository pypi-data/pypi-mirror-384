# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts the command to download the AMIRIS executable and example data."""

import logging as log
import os
import shutil
import zipfile
from enum import Enum, auto
from pathlib import Path
from urllib.error import HTTPError

import wget

from amirispy.source.exception import AMIRISError
from amirispy.source.files import ensure_folder_exists, check_if_write_access
from amirispy.source.logs import log_and_print, log_critical, log_error
from amirispy.source.java import check_java_installation, check_java_version

MSG_SKIPPED_DOWNLOAD = "Skipped download of {} due to option '-m/--mode {}'"
URL_EXAMPLES = "https://gitlab.com/dlr-ve/esy/amiris/examples/-/archive/main/examples-main.zip"

DEPLOY_URL = "https://gitlab.com/dlr-ve/esy/amiris/amiris/-/artifacts"
ERR_URL_INVALID = "Download failed with error: '{}'. Please find latest deploy artifacts here: {}."
ERR_FILE_EXISTS = "'{}' already exists in '{}'. Use `-f/--force` to override anyway."
ERR_NOT_A_ZIP_FILE = "Downloaded file is not a zip file: Could not unzip."


class DownloadMode(Enum):
    """Download `mode` options."""

    ALL = auto()
    MODEL = auto()
    EXAMPLES = auto()


def download_amiris(url: str, target_folder: Path, force: bool, mode: str) -> None:
    """Download and unzip AMIRIS from given url, overwriting existing AMIRIS file if `force` is enabled.

    Args:
        url: where to download packaged AMIRIS file from
        target_folder: folder where to save the AMIRIS to
        force: flag to overwrite existing AMIRIS downloads of same version and existing examples
        mode: mode of download (all, model only, examples only)

    Raises:
        AMIRISError: if any check fails, logged with level "WARNING"
    """

    ensure_folder_exists(target_folder)
    check_if_write_access(target_folder)

    mode = DownloadMode[mode.upper()]
    if mode == DownloadMode.ALL or mode == DownloadMode.MODEL:
        _conduct_model_download(url, target_folder, force)
    else:
        log.info(MSG_SKIPPED_DOWNLOAD.format("AMIRIS model", mode.name.lower()))

    if mode == DownloadMode.ALL or mode == DownloadMode.EXAMPLES:
        _conduct_example_download(target_folder, force)
    else:
        log.info(MSG_SKIPPED_DOWNLOAD.format("examples", mode.name.lower()))

    check_java_installation()
    check_java_version()


def _conduct_model_download(url: str, target_folder: Path, force: bool) -> None:
    """Downloads and extracts AMIRIS from `url` to `target_folder`. Overwrites existing files if `force` is True.

    Args:
        url: where to download packaged AMIRIS file from
        target_folder: folder where to save the AMIRIS to
        force: flag to overwrite existing AMIRIS files

    Raises:
        AMIRISError: if download is not successful; logged with level "CRITICAL"
    """
    download_file_path = Path(target_folder, "amiris.zip")
    log.info("Starting download of AMIRIS")
    try:
        wget.download(url=url, out=str(download_file_path), bar=progress_bar)
    except HTTPError as e:
        raise log_critical(AMIRISError(ERR_URL_INVALID.format(e, DEPLOY_URL)))
    log.info(f"Downloaded file to '{download_file_path}'")
    _unzip(download_file_path, force, target_folder)
    log_and_print(f"AMIRIS download to '{target_folder}' completed.")


def _unzip(download_file_path, force, target_folder) -> None:
    """Unzips downloaded file.

    Args:
        download_file_path: path to zip file
        target_folder: folder where to save the AMIRIS to
        force: flag to overwrite existing AMIRIS files

    Raises:
        AMIRISError: if unzipping is not successful; logged with level "ERROR"
    """
    if zipfile.is_zipfile(download_file_path):
        with zipfile.ZipFile(download_file_path, "r") as zip_ref:
            zip_ref.extractall(target_folder)
        os.remove(download_file_path)

        if force:
            for file in target_folder.glob("target/*with-dependencies.jar"):
                shutil.copy(src=str(file), dst=target_folder)
            log.info(f"Unzipped file content to '{target_folder}'")
        else:
            for file in target_folder.glob("target/*with-dependencies.jar"):
                try:
                    shutil.move(src=str(file), dst=target_folder)
                except shutil.Error:
                    log.error(ERR_FILE_EXISTS.format(file.name, target_folder))
        shutil.rmtree(Path(target_folder, "target"))
    else:
        raise log_error(AMIRISError(ERR_NOT_A_ZIP_FILE))


def progress_bar(current, total, _) -> str:
    """Progress bar that adds a newline in the end."""
    progress_message = "Download status: "
    if total < 0:
        progress_message += "unknown"
    elif current < total:
        progress_message += "%d%% [%d / %d] bytes" % (current / total * 100, current, total)
    else:
        progress_message += "done\n"
    return progress_message


def _conduct_example_download(target_folder: Path, force: bool) -> None:
    """Downloads and extracts examples for AMIRIS to `target_folder`. Overwrites existing examples if `force` is True.

    Args:
        target_folder: folder where to save the examples to
        force: if True, existing examples are overwritten
    """
    download_file_path = Path(target_folder, "examples.zip")
    log.info("Starting download of examples")
    wget.download(url=URL_EXAMPLES, out=str(download_file_path), bar=progress_bar)
    print("")  # fix broken progress bar that misses the newline
    log.info(f"Downloaded examples to '{download_file_path}'")

    if Path(target_folder, "examples").exists() and not force:
        log.error(f"'examples' already exists in '{target_folder}'. Use `-f/--force` to override anyway.")
    else:
        if zipfile.is_zipfile(download_file_path):
            with zipfile.ZipFile(download_file_path, "r") as zip_ref:
                zip_ref.extractall(target_folder)
        else:
            log.info("Downloaded file is not a zip file: Could not unzip")
        shutil.move(src=f"{target_folder}/examples-main", dst=f"{target_folder}/examples")

        log_and_print(f"Examples download to '{target_folder}/examples' completed.")
    os.remove(download_file_path)
