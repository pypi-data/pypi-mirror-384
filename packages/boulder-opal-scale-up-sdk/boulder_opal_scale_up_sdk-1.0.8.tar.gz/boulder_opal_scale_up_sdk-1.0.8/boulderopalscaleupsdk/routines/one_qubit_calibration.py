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

from .common import Routine


class OneQubitCalibration(Routine):
    """
    Parameters for running one qubit calibration routine.

    Attributes
    ----------
    transmon : str
        The reference for the transmon to target.
    gate : "sx" or "x"
        The gate to calibrate.
    repetitions : list[int] or None, optional
        List of repetition counts for the calibration experiment.
        If not provided, a set of repetitions will be chosen based on the gate.
    """

    _routine_name: str = PrivateAttr("one_qubit_calibration")

    transmon: str
    gate: Literal["x", "sx"]
    repetitions: list[int] | None = None
