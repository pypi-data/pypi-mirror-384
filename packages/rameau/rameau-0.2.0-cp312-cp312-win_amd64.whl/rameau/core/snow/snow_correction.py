# Copyright 2025, BRGM
# 
# This file is part of Rameau.
# 
# Rameau is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# Rameau is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# Rameau. If not, see <https://www.gnu.org/licenses/>.
#
"""
Correction parameters applied to snow melting physical processes.
"""

from rameau.wrapper import CSnowCorrection

from rameau.core import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _DerivedTypeDecriptor

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter

class SnowCorrectionParameters(AbstractWrapper):
    """Correction parameters applied to snow melting physical processes.
    
    Parameters
    ----------
    pet : `dict` or `Parameter`, optional
        Correction factor on |PET| used for snow sublimation (%).

    rainfall : `dict` or `Parameter`, optional
        Correction factor for snow melting by rain calories (%).

    temperature : `dict` or `Parameter`, optional
        Temperature correction term (°C). Corrects any discrepancy affecting
        the model input temperature.
    
    Returns
    -------
    `SnowCorrectionParameters`
    """

    _computed_attributes = "pet", "temperature", "rainfall"
    _c_class = CSnowCorrection
    rainfall: Parameter = _DerivedTypeDecriptor(
        0, Parameter,
        doc="Correction factor for snow melting by rain calories (%)."
    ) # type: ignore
    pet: Parameter = _DerivedTypeDecriptor(
        1, Parameter,
        doc=(
            "Correction factor on Potential Evapotranspiration used for "
            "snow sublimation (%)."
        )
    ) # type: ignore
    temperature: Parameter = _DerivedTypeDecriptor(
        2, Parameter,
        doc=(
            "Temperature correction term (°C). Corrects any discrepancy "
            "affecting the model input temperature."
        )
    ) # type: ignore

    def __init__(
            self,
            pet: ParameterType = None,
            rainfall: ParameterType = None,
            temperature: ParameterType = None,
        ) -> None: 
        self._init_c()

        if pet is not None:
            self.pet = _build_parameter(pet)
        if temperature is not None:
            self.temperature = _build_parameter(temperature)
        if rainfall is not None:
            self.rainfall = _build_parameter(rainfall)