# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: CC0-1.0

"""Contains the main script and its subcommands called by CLI."""

from .amiris import amiris_cli
from ..source.exception import AMIRISError


def amiris():
    try:
        amiris_cli()
    except AMIRISError as e:
        raise SystemExit(1) from e
