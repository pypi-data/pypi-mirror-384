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

from .common import Experiment, LinspaceIterable, RangeIterable


class CZSpectroscopyByBias(Experiment):
    """
    Parameters for running a CZ spectroscopy by bias experiment.

    Attributes
    ----------
    control_transmon : str
        The reference for the transmon to use as control.
    target_transmon : str
        The reference for the transmon to use as target.
    vps : LinspaceIterable
        The voltage points to sample, in volts.
    coupler_flux_vp : float
        The flux voltage point for the coupler, in volts.
    durations_ns : RangeIterable, optional
        The pulse durations to sample, in nanoseconds.
        Defaults to RangeIterable(start=16, stop=200, step=8).
    prep_padding_ns : int, optional
        The padding to apply before the CZ pulse, in nanoseconds.
        Defaults to 16 ns.
    measurement_padding_ns : int, optional
        The padding to apply after the CZ pulse, in nanoseconds.
        Defaults to 16 ns.
    recycle_delay_ns : float, optional
        The delay between consecutive shots, in nanoseconds.
        Defaults to 500,000 ns.
    shot_count : int, optional
        The number of shots to take.
        Defaults to 200.
    update : "auto" or "off" or "prompt", optional
        How the device should be updated after an experiment run. Defaults to auto.
    """

    _experiment_name: str = PrivateAttr("cz_spectroscopy_by_bias")

    control_transmon: str
    target_transmon: str
    vps: LinspaceIterable
    coupler_flux_vp: float
    durations_ns: RangeIterable = RangeIterable(start=16, stop=200, step=8)
    prep_padding_ns: int = 16
    measurement_padding_ns: int = 16
    recycle_delay_ns: int = 500_000
    shot_count: int = 200
    update: Literal["auto", "off", "prompt"] = "auto"
