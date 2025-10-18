# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum


class ReceiverName(Enum):
    """The name of a supported receiver.

    :ivar RSP1A: SDRPlay RSP1A
    :ivar RSPDUO: SDRPlay RSPduo
    :ivar RSPDX: SDRPlay RSPdx
    :ivar SIGNAL_GENERATOR: A synthetic signal generator.
    :ivar B200MINI: USRP B200mini.
    :ivar HACKRFONE: Hack RF One.
    :ivar RTLSDR: RTL-SDR.
    :ivar CUSTOM: A custom receiver, which starts with no operating modes.
    """

    SIGNAL_GENERATOR = "signal_generator"
    RSP1A = "rsp1a"
    RSPDUO = "rspduo"
    RSPDX = "rspdx"
    B200MINI = "b200mini"
    HACKRFONE = "hackrfone"
    RTLSDR = "rtlsdr"
    CUSTOM = "custom"
