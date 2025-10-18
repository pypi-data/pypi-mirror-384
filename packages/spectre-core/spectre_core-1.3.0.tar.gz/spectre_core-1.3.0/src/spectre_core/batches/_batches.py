# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from typing import Optional, TypeVar, Type, Generic, Iterator
from collections import OrderedDict
from datetime import datetime

from spectre_core.config import TimeFormat
from spectre_core.spectrograms import Spectrogram, time_chop, join_spectrograms
from spectre_core.config import get_batches_dir_path
from spectre_core.exceptions import BatchNotFoundError
from ._base import BaseBatch, parse_batch_file_name

T = TypeVar("T", bound=BaseBatch)


class Batches(Generic[T]):
    """Managed collection of `Batch` instances for a given tag. Provides a simple
    interface for read operations on batched data files."""

    def __init__(
        self,
        tag: str,
        batch_cls: Type[T],
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
    ) -> None:
        """Initialise a `Batches` instance.

        :param tag: The batch name tag.
        :param batch_cls: The `Batch` class used to read data files tagged by `tag`.
        :param year: Filter batch files under a numeric year. Defaults to None.
        :param month: Filter batch files under a numeric month. Defaults to None.
        :param day: Filter batch files under a numeric day. Defaults to None.
        """
        self._tag = tag
        self._batch_cls = batch_cls
        self._batch_map: dict[str, T] = OrderedDict()
        self.set_date(year, month, day)

    @property
    def tag(self) -> str:
        """The batch name tag."""
        return self._tag

    @property
    def batch_cls(self) -> Type[T]:
        """The `Batch` class used to read the batched files."""
        return self._batch_cls

    @property
    def year(self) -> Optional[int]:
        """The numeric year, to filter batch files."""
        return self._year

    @property
    def month(self) -> Optional[int]:
        """The numeric month of the year, to filter batch files."""
        return self._month

    @property
    def day(self) -> Optional[int]:
        """The numeric day of the year, to filter batch files."""
        return self._day

    @property
    def batches_dir_path(self) -> str:
        """The shared ancestral path for all the batches. `Batches` recursively searches
        this directory to find all batches whose batch name contains `tag`."""
        return get_batches_dir_path(self.year, self.month, self.day)

    @property
    def batch_list(self) -> list[T]:
        """A list of all batches found within `batches_dir_path`."""
        return list(self._batch_map.values())

    @property
    def start_times(self) -> list[str]:
        """The start times of each batch found within `batches_dir_path`."""
        return list(self._batch_map.keys())

    @property
    def num_batches(self) -> int:
        """The total number of batches found within `batches_dir_path`."""
        return len(self.batch_list)

    def set_date(
        self, year: Optional[int], month: Optional[int], day: Optional[int]
    ) -> None:
        """Reset `batches_dir_path` according to the numeric date, and refresh the list
        of available batches.

        :param year: Filter by the numeric year.
        :param month: Filter by the numeric month of the year.
        :param day: Filter by the numeric day of the month.
        """
        self._year = year
        self._month = month
        self._day = day
        self.update()

    def update(self) -> None:
        """Perform a fresh search all files in `batches_dir_path` for batches
        with `tag` in the batch name."""
        # reset cache
        self._batch_map = OrderedDict()

        # get a list of all batch file names in the batches directory path
        batch_file_names = [
            f for (_, _, files) in os.walk(self.batches_dir_path) for f in files
        ]
        for batch_file_name in batch_file_names:
            start_time, tag, _ = parse_batch_file_name(batch_file_name)
            if tag == self._tag:
                self._batch_map[start_time] = self.batch_cls(start_time, tag)

        self._batch_map = OrderedDict(sorted(self._batch_map.items()))

    def __iter__(self) -> Iterator[T]:
        """Iterate over the stored batch instances."""
        yield from self.batch_list

    def __len__(self):
        return self.num_batches

    def _get_from_start_time(self, start_time: str) -> T:
        """Find and return the `Batch` instance based on the string formatted start time."""
        try:
            return self._batch_map[start_time]
        except KeyError:
            raise BatchNotFoundError(
                f"Batch with start time {start_time} could not be found within {self.batches_dir_path}"
            )

    def _get_from_index(self, index: int) -> T:
        """Find and return the `Batch` instance based on its numeric index.

        Batches are ordered sequentially in time, so index `0` corresponds to the oldest
        `Batch` with respect to the start time.
        """
        if self.num_batches == 0:
            raise BatchNotFoundError("No batches are available")
        elif index > self.num_batches:
            raise IndexError(
                f"Index '{index}' is greater than the number of batches '{self.num_batches}'"
            )
        return self.batch_list[index]

    def __getitem__(self, subscript: str | int) -> T:
        """Get a `Batch` instanced based on either the start time or chronological index.

        :param subscript: If the subscript is a string, interpreted as a formatted start time.
        If the subscript is an integer, it is interpreted as a chronological index.
        :return: The corresponding `BaseBatch` subclass.
        """
        if isinstance(subscript, str):
            return self._get_from_start_time(subscript)
        elif isinstance(subscript, int):
            return self._get_from_index(subscript)

    def __validate_range(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> None:
        if start_datetime == end_datetime:
            raise ValueError(
                f"The start and end time must be different. "
                f"Got start time {start_datetime}, "
                f"and end time {end_datetime}"
            )

        if start_datetime > end_datetime:
            raise ValueError(
                f"The start time must be less than the end time. "
                f"Got start time {start_datetime}, "
                f"and end time {end_datetime}"
            )

    def get_spectrogram(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> Spectrogram:
        """
        Retrieve a spectrogram spanning the specified time range.

        :param start_datetime: The start time of the range (inclusive).
        :param end_datetime: The end time of the range (inclusive).
        :raises FileNotFoundError: If no spectrogram data is available within the specified time range.
        :raise ValueError: If the start time is not less than the end time.
        :return: A spectrogram created by stitching together data from all matching batches.
        """
        self.__validate_range(start_datetime, end_datetime)
        batches_in_range = self.get_batches_in_range(start_datetime, end_datetime)
        spectrograms = [
            batch.read_spectrogram()
            for batch in batches_in_range
            if batch.spectrogram_file.exists
        ]

        if not spectrograms:
            raise FileNotFoundError(
                f"No spectrogram data found for the time range {start_datetime} to {end_datetime}."
            )
        return time_chop(join_spectrograms(spectrograms), start_datetime, end_datetime)

    def get_batches_in_range(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> list[T]:
        """Get batches that overlap with the input time range.

        The end time of each batch is upper bounded by the start time of the next,
        since they cannot overlap. The final batch is treated as ending at `datetime.max`
        since there is no batch after it to provide that upper bound.

        :param start_datetime: The start time of the range (inclusive).
        :param end_datetime: The end time of the range (inclusive).
        :raise ValueError: If the start time is not less than the end time.
        :return: A list of `Batch` instances that fall within the specified time range.
        """
        self.__validate_range(start_datetime, end_datetime)
        filtered_batches = []
        batch_datetimes = [
            datetime.strptime(t, TimeFormat.DATETIME) for t in self.start_times
        ]
        for idx, batch in enumerate(self):
            this_start = batch_datetimes[idx]
            next_start = (
                batch_datetimes[idx + 1]
                if idx + 1 < len(batch_datetimes)
                else datetime.max
            )
            if start_datetime < next_start and this_start <= end_datetime:
                filtered_batches.append(batch)

        return filtered_batches
