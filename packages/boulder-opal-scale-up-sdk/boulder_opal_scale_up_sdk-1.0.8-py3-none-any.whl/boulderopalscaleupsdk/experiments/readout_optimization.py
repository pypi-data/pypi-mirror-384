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

from .common import (
    CWSIterable,
    Experiment,
    HypIterable,
    LinspaceIterable,
    RangeIterable,
)


class ReadoutOptimization(Experiment):
    """
    Parameters for optimizing the readout classifier.

    Attributes
    ----------
    transmon : str
        The reference for the transmon to target.
    frequencies : list[int] or LinspaceIterable or RangeIterable or CWSIterable or HypIterable
        The readout frequencies to sweep, in Hz.
    amplitudes : list[float]
        The readout amplitudes to sweep.
    recycle_delay_ns : int, optional
        The delay between consecutive shots, in nanoseconds. Defaults to 200,000 ns.
    shot_count : int, optional
        The number of shots to take. Defaults to 5,000.
    run_mixer_calibration: bool, optional
        Whether to run mixer calibrations before running a program. Defaults to False.
    update : "auto" or "off", optional
        How the device should be updated after an experiment run. Defaults to auto.
    """

    _experiment_name: str = PrivateAttr("readout_optimization")

    transmon: str
    frequencies: list[int] | LinspaceIterable | RangeIterable | CWSIterable | HypIterable
    amplitudes: list[float]
    recycle_delay_ns: int = 200_000
    shot_count: int = 5000
    run_mixer_calibration: bool = False
    update: Literal["auto", "off"] = "auto"
