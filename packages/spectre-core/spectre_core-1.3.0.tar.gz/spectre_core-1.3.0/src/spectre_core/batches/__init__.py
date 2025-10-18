# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""IO operations on batched data files."""

from .plugins._batch_keys import BatchKey

# register decorators take effect on import
from .plugins._iq_stream import IQStreamBatch, IQMetadata
from .plugins._callisto import CallistoBatch

from ._base import (
    BaseBatch,
    BatchFile,
    parse_batch_file_name,
    parse_batch_base_file_name,
)
from ._batches import Batches
from ._factory import get_batch_cls, get_batch_cls_from_tag

__all__ = [
    "IQStreamBatch",
    "IQMetadata",
    "CallistoBatch",
    "BaseBatch",
    "BatchFile",
    "Batches",
    "get_batch_cls",
    "BatchKey",
    "get_batch_cls_from_tag",
    "parse_batch_file_name",
]

# To be deprecated.
__all__ += [
    "parse_batch_base_file_name",
]
