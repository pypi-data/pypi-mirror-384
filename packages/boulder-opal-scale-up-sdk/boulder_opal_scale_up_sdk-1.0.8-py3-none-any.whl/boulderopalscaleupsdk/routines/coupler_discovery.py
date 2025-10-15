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

from pydantic import PrivateAttr

from .common import Routine


class CouplerDiscovery(Routine):
    """
    Parameters for running a coupler discovery routine.

    Attributes
    ----------
    control_transmon : str
        The reference for the transmon to use as control.
    target_transmon : str
        The reference for the transmon to use as target.
    biases : list[float]
        The biases to sweep the coupler through.
    """

    _routine_name: str = PrivateAttr("coupler_discovery")

    control_transmon: str
    target_transmon: str
    biases: list[float]
