# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.

from typing import Literal

from pydantic import PrivateAttr

from .common import Experiment
from .waveforms import ConstantWaveform


class ReadoutClassifier(Experiment):
    """
    Parameters for training a readout classifier.

    This does not optimize the readout pulse itself.
    The measure waveform is fixed (provided or using the device's default).
    To optimize the readout pulse use ReadoutOptimization.

    Attributes
    ----------
    transmon : str
        The reference for the transmon to target.
    recycle_delay_ns : int, optional
        The delay between consecutive shots, in nanoseconds. Defaults to 200,000 ns.
    shot_count : int, optional
        The number of shots to take. Defaults to 5,000.
    measure_waveform : ConstantWaveform or None, optional
        The waveform to use for the measurement pulse.
        Defaults to the measurement defcal.
    run_mixer_calibration: bool, optional
        Whether to run mixer calibrations before running a program. Defaults to False.
    update : "auto" or "off" or "prompt", optional
        How the device should be updated after an experiment run. Defaults to auto.
    """

    _experiment_name: str = PrivateAttr("readout_classifier")

    transmon: str
    recycle_delay_ns: int = 200_000
    shot_count: int = 5000
    measure_waveform: ConstantWaveform | None = None
    run_mixer_calibration: bool = False
    update: Literal["auto", "off", "prompt"] = "auto"
