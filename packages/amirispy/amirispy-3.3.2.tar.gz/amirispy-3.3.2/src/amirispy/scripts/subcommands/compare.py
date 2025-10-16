# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts the command to compare two AMIRIS result folders."""

import logging as log
from pathlib import Path
from typing import List

from amirispy.source.file_comparison import match_files, compare_files
from amirispy.source.files import get_all_csv_files_in_folder_except
from amirispy.source.logs import log_and_print


def compare_results(folder_expected: Path, folder_to_test: Path, ignore_list: List[str] = None) -> None:
    """Compares content of two folders with AMIRIS results in CSV format for equivalence.

    Args:
        folder_expected: folder with expected results
        folder_to_test: folder with results to test against expected results
        ignore_list: optional list of file names to ignore
    """

    expected_files = get_all_csv_files_in_folder_except(folder_expected, ignore_list)
    test_files = get_all_csv_files_in_folder_except(folder_to_test, ignore_list)
    file_pairs = match_files(expected_files, test_files)

    log.info(f"Checking {len(expected_files)} expected files...")
    results = {}
    for expected, to_test in file_pairs.items():
        if to_test:
            results[expected] = compare_files(expected, to_test)
        else:
            results[expected] = f"Missing file in test folder: {expected.stem}"

    differences_found = False
    for file, differences in results.items():
        if differences:
            differences_found = True
            log_and_print(f"FAIL: Found differences for {file.stem}: {differences}")

    if not differences_found:
        log_and_print("PASS: Found no significant differences for any expected pair of files.")
