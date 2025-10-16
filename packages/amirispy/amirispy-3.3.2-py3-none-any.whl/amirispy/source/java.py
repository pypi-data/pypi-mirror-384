# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Holds methods to check installed version of Java."""

from __future__ import annotations
import logging as log
import re
import shutil
import subprocess

from amirispy.source.exception import AMIRISError
from amirispy.source.logs import log_critical

_ERR_NO_JAVA = "No Java installation found. See {} for further instructions."
_ERR_JAVA_VERSION = "Local Java version '{}' does not match requirements '>{}'."
_ERR_JAVA_UNKNOWN = "Local Java version could not be determined. Ensure to have at least Java '{}' installed."
_URL_INSTALLATION_INSTRUCTIONS = "https://gitlab.com/dlr-ve/esy/amiris/amiris-py#further-requirements"

JAVA_VERSION_STRING_PATTERN = r'version "([1-9][0-9]*)((\.0)*\.[1-9][0-9]*)*"'
JAVA_VERSION_MINIMUM = 11


def check_java_installation(raise_exception: bool = False) -> None:
    """Checks if the java command is available.

    Args:
        raise_exception: if True, an Exception is raised, else a warning

    Raises:
        AMIRISError: if Java installation is not found; logged with level "WARNING" (default) or "CRITICAL"
    """
    if not shutil.which("java"):
        if raise_exception:
            raise log_critical(AMIRISError(_ERR_NO_JAVA.format(_URL_INSTALLATION_INSTRUCTIONS)))
        log.warning(_ERR_NO_JAVA.format(_URL_INSTALLATION_INSTRUCTIONS))


def check_java_version(raise_exception: bool = False) -> None:
    """Checks if Java version is compatible with requirements of FAME.

    Args:
        raise_exception: if True, an Exception is raised, else a warning

     Raises:
        AMIRISError: if Java version is not compatible or not found; logged with level "WARNING" (default) or "CRITICAL"
    """
    version_raw = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT)
    if error := _get_error_on_version_not_fulfilled(str(version_raw)):
        if raise_exception:
            raise log_critical(AMIRISError(error))
        log.warning(error)


def _get_error_on_version_not_fulfilled(version_string: str) -> str | None:
    """Searches for Java version pattern in given string and checks if minimum version requirement is satisfied.

    Args:
        version_string: string returned by "java -version" command

    Returns:
        error string if version string is not found, invalid or does not match requirements,
            or None if version is sufficient
    """
    match: re.Match[str] | None = re.search(JAVA_VERSION_STRING_PATTERN, version_string)
    if not match:
        return _ERR_JAVA_UNKNOWN.format(JAVA_VERSION_MINIMUM)
    version_number = int(match.groups()[0])

    if version_number < JAVA_VERSION_MINIMUM:
        return _ERR_JAVA_VERSION.format(version_number, JAVA_VERSION_MINIMUM)
    return None


def check_java(skip: bool) -> None:
    """Checks both Java installation and version if not `skip`.

    Args:
        skip: if enabled, checks are skipped

    Raises:
          AMIRISError: if any check fails; logged with level "CRITICAL"
    """
    if not skip:
        check_java_installation(raise_exception=True)
        check_java_version(raise_exception=True)
