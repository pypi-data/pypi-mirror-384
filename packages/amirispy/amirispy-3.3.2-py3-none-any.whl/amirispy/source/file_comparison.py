# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Hosts methods to compare content of folders and files."""

import logging
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd

_MISSING_EXPECTED_FILE = "Expected file {} was not found among files in the test folder."
_TEST_FILE_UNMATCHED = "Missing file to compare with file {} found in test folder."
_VALUE_DISALLOWED = "Found non-numeric and non-string value."
_ALL_VALUES_EQUIVALENT = "Content of files is equivalent for {}."
_VALUES_NOT_EQUIVALENT = "Files are not equivalent for {}."
_SHAPE_MISMATCH = "File to test {} has different shape than expected: {}"


def match_files(expected_files: List[Path], test_files: List[Path]) -> Dict[Path, Path]:
    """Compares files in given paths for equivalence.

    Args:
        expected_files: paths of expected files
        test_files: path of files for text

    Returns:
        Match of each expected file to its test file, or None if test file is not found
    """
    expected_pairs = {item.stem.upper(): item for item in expected_files}
    test_pairs = {item.stem.upper(): item for item in test_files}
    result = {}
    for expected_stem, expected_file in expected_pairs.items():
        if expected_stem in test_pairs.keys():
            result[expected_file] = test_pairs.pop(expected_stem)
        else:
            result[expected_file] = ""
            logging.error(_MISSING_EXPECTED_FILE.format(expected_stem))
    if len(test_pairs) > 0:
        for test_stem in test_pairs.keys():
            logging.warning(_TEST_FILE_UNMATCHED.format(test_stem))
    return result


def compare_files(expected: Path, to_test: Path) -> str:
    """Compares two csv files for equivalence and logs "ERROR" if files are not equivalent.

    Args:
        expected: file with expected data
        to_test: file with data to test

    Returns:
        Empty string if everything matched, else details on the differences
    """
    expected_df = read_file_and_sort_df(expected)
    test_df = read_file_and_sort_df(to_test)
    result = ""
    if expected_df.shape != test_df.shape:
        logging.error(_SHAPE_MISMATCH.format(to_test.stem, expected_df.shape))
        result = analyse_shape_difference(expected_df.shape, test_df.shape)
    else:
        all_values_compared = np.isclose(test_df, expected_df)
        if np.all(all_values_compared):
            logging.info(_ALL_VALUES_EQUIVALENT.format(to_test.stem))
        else:
            logging.error(_VALUES_NOT_EQUIVALENT.format(to_test.stem))
            result = analyse_row_difference(test_df, all_values_compared)
    return result


def analyse_shape_difference(expected_shape: Tuple[int, int], test_shape: Tuple[int, int]) -> str:
    """Analyses difference between two two-dimensional dataframe shapes.

    Args:
        expected_shape: reference shape
        test_shape: shape to check against the reference

    Returns:
        description of the shape difference
    """
    row_delta = test_shape[0] - expected_shape[0]
    column_delta = test_shape[1] - expected_shape[1]
    result = ""
    if row_delta != 0:
        result += f"Test file {'has extra' if row_delta > 0 else 'misses' } {abs(row_delta)} row(s). "
    if column_delta != 0:
        result += f"Test file {'has extra' if row_delta > 0 else 'misses'} {abs(column_delta)} column(s). "
    return result


def analyse_row_difference(test_data: pd.DataFrame, comparison_result: np.ndarray) -> str:
    """Returns list of rows in the given test data frame that contain at least on mismatch in the comparison.

    Args:
        test_data: original test data set with proper index
        comparison_result: array containing True or False for each row and column, where False indicates a mismatch to
            the reference data set

    Returns:
        String listing all row numbers of the test data set that did not match the reference data
    """
    compare_df = pd.DataFrame(comparison_result, index=test_data.index)
    filtered = compare_df[(compare_df == False).any(axis=1)]  # noqa
    adjust_line_count_for_header_and_start_1 = [i + 2 for i in filtered.index.to_list()]
    return f"Deviations in test file line(s): {adjust_line_count_for_header_and_start_1}"


def read_file_and_sort_df(file: Path) -> pd.DataFrame:
    """Reads given file to data frame.

    Replaces missing values with 0, converts strings to numbers and sorts from left to right columns.

    Args:
        file: file to read

    Returns:
        sorted data frame with a numeric representation of given file's content (NaNs replaced by 0)
    """
    df = pd.read_csv(file, sep=";")
    df.fillna(0, inplace=True)
    df = df.apply(string_to_number)
    return df.sort_values(by=list(df.columns.values))


def string_to_number(series: pd.Series) -> pd.Series:
    """Converts pandas series of any numeric or string values to series of numeric values.

    Each string is converted to a single number: sum of its ascii values.
    Thus, identical strings always result in same number.
    However, different strings may also result in same number.
    Think of it as a very simple numeric hash function.
    Does not change numeric values in series.

    Args:
        series: series with numeric values and possibly mixed with strings

    Returns:
        Deterministic numeric series
    """
    return series.apply(lambda x: sum([ord(char) for char in x]) if isinstance(x, str) else x)
