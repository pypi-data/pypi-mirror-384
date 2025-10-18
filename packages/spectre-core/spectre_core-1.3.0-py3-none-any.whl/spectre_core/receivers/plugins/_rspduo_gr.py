# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._gr import spectre_top_block

from gnuradio import spectre
from gnuradio import sdrplay3


@dataclass(frozen=True)
class Port:
    """Specifies one of the antenna ports on the RSPduo.

    These are easier to type in the CLI tool, than the values we must pass to `gr-sdrplay3`.
    Namely 'Tuner 1 50' ohm and 'Tuner 2 50 ohm'.
    """

    TUNER_1 = "tuner_1"
    TUNER_2 = "tuner_2"


def _map_port(antenna_port: str | None) -> str:
    """Maps the CLI-typeable port, to the one used in the constructor for the RSPduo block in the gr-sdrplay3 OOT module."""
    if antenna_port == Port.TUNER_1:
        return "Tuner 1 50 ohm"
    elif antenna_port == Port.TUNER_2:
        return "Tuner 2 50 ohm"
    else:
        raise ValueError(f"{antenna_port} is not a valid antenna port.")


class fixed_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Unpack the capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        center_freq = parameters.get_parameter_value(PName.CENTER_FREQUENCY)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)
        if_gain = parameters.get_parameter_value(PName.IF_GAIN)
        rf_gain = parameters.get_parameter_value(PName.RF_GAIN)
        antenna_port = parameters.get_parameter_value(PName.ANTENNA_PORT)

        # Blocks
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, sample_rate
        )
        self.sdrplay3_rspduo = sdrplay3.rspduo(
            "",
            rspduo_mode="Single Tuner",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rspduo.set_sample_rate(sample_rate)
        self.sdrplay3_rspduo.set_center_freq(center_freq)
        self.sdrplay3_rspduo.set_bandwidth(bandwidth)
        self.sdrplay3_rspduo.set_antenna(_map_port(antenna_port))
        self.sdrplay3_rspduo.set_gain_mode(False)
        self.sdrplay3_rspduo.set_gain(if_gain, "IF")
        self.sdrplay3_rspduo.set_gain(rf_gain, "RF")
        self.sdrplay3_rspduo.set_freq_corr(0)
        self.sdrplay3_rspduo.set_dc_offset_mode(False)
        self.sdrplay3_rspduo.set_iq_balance_mode(False)
        self.sdrplay3_rspduo.set_agc_setpoint(-30)
        self.sdrplay3_rspduo.set_rf_notch_filter(False)
        self.sdrplay3_rspduo.set_dab_notch_filter(False)
        self.sdrplay3_rspduo.set_am_notch_filter(False)
        self.sdrplay3_rspduo.set_biasT(False)
        self.sdrplay3_rspduo.set_debug_mode(False)
        self.sdrplay3_rspduo.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspduo.set_show_gain_changes(False)

        # Connections
        self.connect((self.sdrplay3_rspduo, 0), (self.spectre_batched_file_sink, 0))


class swept_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:

        # Unpack the capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)
        min_frequency = parameters.get_parameter_value(PName.MIN_FREQUENCY)
        max_frequency = parameters.get_parameter_value(PName.MAX_FREQUENCY)
        frequency_step = parameters.get_parameter_value(PName.FREQUENCY_STEP)
        samples_per_step = parameters.get_parameter_value(PName.SAMPLES_PER_STEP)
        if_gain = parameters.get_parameter_value(PName.IF_GAIN)
        rf_gain = parameters.get_parameter_value(PName.RF_GAIN)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        antenna_port = parameters.get_parameter_value(PName.ANTENNA_PORT)

        # Blocks
        self.spectre_sweep_driver = spectre.sweep_driver(
            min_frequency,
            max_frequency,
            frequency_step,
            sample_rate,
            samples_per_step,
            "freq",
        )
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(),
            tag,
            batch_size,
            sample_rate,
            True,
            "freq",
            min_frequency,
        )
        self.sdrplay3_rspduo = sdrplay3.rspduo(
            "",
            rspduo_mode="Single Tuner",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rspduo.set_sample_rate(sample_rate, True)
        self.sdrplay3_rspduo.set_center_freq(min_frequency, True)
        self.sdrplay3_rspduo.set_bandwidth(bandwidth)
        self.sdrplay3_rspduo.set_antenna(_map_port(antenna_port))
        self.sdrplay3_rspduo.set_gain_mode(False)
        self.sdrplay3_rspduo.set_gain(if_gain, "IF", True)
        self.sdrplay3_rspduo.set_gain(rf_gain, "RF", True)
        self.sdrplay3_rspduo.set_freq_corr(0)
        self.sdrplay3_rspduo.set_dc_offset_mode(False)
        self.sdrplay3_rspduo.set_iq_balance_mode(False)
        self.sdrplay3_rspduo.set_agc_setpoint(-30)
        self.sdrplay3_rspduo.set_rf_notch_filter(False)
        self.sdrplay3_rspduo.set_dab_notch_filter(False)
        self.sdrplay3_rspduo.set_am_notch_filter(False)
        self.sdrplay3_rspduo.set_biasT(False)
        self.sdrplay3_rspduo.set_stream_tags(True)
        self.sdrplay3_rspduo.set_debug_mode(False)
        self.sdrplay3_rspduo.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspduo.set_show_gain_changes(False)

        # Connections
        self.msg_connect(
            (self.spectre_sweep_driver, "retune_command"),
            (self.sdrplay3_rspduo, "command"),
        )
        self.connect((self.sdrplay3_rspduo, 0), (self.spectre_batched_file_sink, 0))
        self.connect((self.sdrplay3_rspduo, 0), (self.spectre_sweep_driver, 0))
