# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
File system path definitions.

`spectre` uses the required environment variable `SPECTRE_DATA_DIR_PATH`
and creates three directories inside it:

- `batches`: To hold the batched data files.
- `logs`: To hold log files generated at runtime.
- `configs`: To hold the capture config files.
"""

import os
from typing import Optional


def get_spectre_data_dir_path() -> str:
    """The default ancestral path for all `spectre` file system data.

    :return: The value stored by the `SPECTRE_DATA_DIR_PATH` environment variable.
    """
    _SPECTRE_DATA_DIR_PATH = os.environ.get("SPECTRE_DATA_DIR_PATH", "NOTSET")
    if _SPECTRE_DATA_DIR_PATH == "NOTSET":
        raise ValueError(
            "The environment variable `SPECTRE_DATA_DIR_PATH` must be set."
        )
    return _SPECTRE_DATA_DIR_PATH


def set_spectre_data_dir_path(spectre_data_dir_path: str) -> None:
    """Set the `SPECTRE_DATA_DIR_PATH` environment variable.

    This will override the present value, if it is already set.

    As a side effect, this function will also create the following directories:
        - `spectre_data_dir_path`
        - `spectre_data_dir_path` / batches
        - `spectre_data_dir_path` / configs
        - `spectre_data_dir_path` / logs
    """
    # Update the environment variable
    os.environ["SPECTRE_DATA_DIR_PATH"] = spectre_data_dir_path

    # Create the directories, if they do not already exist.
    os.makedirs(get_spectre_data_dir_path(), exist_ok=True)
    os.makedirs(get_batches_dir_path(), exist_ok=True)
    os.makedirs(get_logs_dir_path(), exist_ok=True)
    os.makedirs(get_configs_dir_path(), exist_ok=True)


def _get_date_based_dir_path(
    base_dir: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
) -> str:
    """Append a date-based directory onto the base directory.

    :param base_dir: The base directory to have the date directory appended to.
    :param year: Numeric year. Defaults to None.
    :param month: Numeric month. Defaults to None.
    :param day: Numeric day. Defaults to None.
    :raises ValueError: If a day is specified without the year or month.
    :raises ValueError: If a month is specified without the year.
    :return: The base directory with optional year, month, and day subdirectories appended.
    """
    if day and not (year and month):
        raise ValueError("A day requires both a month and a year")
    if month and not year:
        raise ValueError("A month requires a year")

    date_dir_components = []
    if year:
        date_dir_components.append(f"{year:04}")
    if month:
        date_dir_components.append(f"{month:02}")
    if day:
        date_dir_components.append(f"{day:02}")

    return os.path.join(base_dir, *date_dir_components)


def get_batches_dir_path(
    year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None
) -> str:
    """The directory in the file system containing the batched data files. Optionally, append
    a date-based directory to the end of the path.

    :param year: The numeric year. Defaults to None.
    :param month: The numeric month. Defaults to None.
    :param day: The numeric day. Defaults to None.
    :return: The directory path for batched data files, optionally with a date-based subdirectory.
    """
    batches_dir_path = os.path.join(get_spectre_data_dir_path(), "batches")
    return _get_date_based_dir_path(batches_dir_path, year, month, day)


def get_logs_dir_path(
    year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None
) -> str:
    """The directory in the file system containing the log files generated at runtime. Optionally, append
    a date-based directory to the end of the path.

    :param year: The numeric year. Defaults to None.
    :param month: The numeric month. Defaults to None.
    :param day: The numeric day. Defaults to None.
    :return: The directory path for log files, optionally with a date-based subdirectory.
    """
    logs_dir_path = os.path.join(get_spectre_data_dir_path(), "logs")
    return _get_date_based_dir_path(logs_dir_path, year, month, day)


def get_configs_dir_path() -> str:
    """The directory in the file system containing the capture configs.

    :return: The directory path for configuration files.
    """
    return os.path.join(get_spectre_data_dir_path(), "configs")


def trim_spectre_data_dir_path(full_path: str) -> str:
    """Remove the `SPECTRE_DATA_DIR_PATH` prefix from a full file path.

    This function returns the relative path of `full_path` with respect to
    `SPECTRE_DATA_DIR_PATH`. It is useful for trimming absolute paths
    to maintain consistency across different environments where the base
    directory might differ.

    :param full_path: The full file path to be trimmed.
    :return: The relative path with `SPECTRE_DATA_DIR_PATH` removed.
    """
    return os.path.relpath(full_path, get_spectre_data_dir_path())


def add_spectre_data_dir_path(rel_path: str) -> str:
    """Prepend the `SPECTRE_DATA_DIR_PATH` prefix to a relative file path.

    This function constructs an absolute path by joining the given relative
    path with `SPECTRE_DATA_DIR_PATH`. It is useful for converting stored
    relative paths back into full paths within the mounted directory.

    :param rel_path: The relative file path to be appended.
    :return: The full file path prefixed with `SPECTRE_DATA_DIR_PATH`.
    """
    return os.path.join(get_spectre_data_dir_path(), rel_path)
