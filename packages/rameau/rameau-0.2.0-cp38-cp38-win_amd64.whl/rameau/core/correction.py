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
Correction parameters.
"""

from rameau.wrapper import CCorrection

from rameau.core import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter
from rameau.core._descriptor import _DerivedTypeDecriptor

class CorrectionParameters(AbstractWrapper):
    """Correction parameters.
    
    Parameters
    ----------
    area: `float` or `dict` or `Parameter`, optional
        Factor correcting the drainage area of the watershed (-). Should be
        optimised only when drainage area is poorly known (e.g. loss in karstic
        watershed, multiple watershed outlets, water source supply).

    pet: `float` or `dict` or `Parameter`, optional
        |PET| correction factor (%) designed to compensate for any poor
        representativeness of observed |PET| data obtained from scattered
        meteorological stations. This correction is applied to all time steps.

    rainfall: `float` or `dict` or `Parameter`, optional
        Rainfall correction factor (%) designed to compensate for any poor
        representativeness of observed rainfall data obtained from scattered
        meteorological stations. This correction is applied both to liquid and
        solid precipitation at all time steps. Should be optimised only when
        rainfall is poorly known (e.g. mountainous areas).
    
    Returns
    -------
    `CorrectionParameters`
    
    Notes
    -----
    The |PET| correction coefficient also takes into account cultural factors
    defining maximum evaporation at a given vegetative stage.
    
    Examples
    --------

    To multiply the drainage area by 1.2 and to increase |PET| by 5% at
    all time steps:

    >>> area = rm.Parameter(value=0.2)
    >>> pet = dict(value=5)
    >>> corrections = rm.CorrectionParameters(area=area, pet=pet)
    >>> round(corrections.area.value, 6)
    0.2
    >>> corrections.pet.value
    5.0

    To optimise the correction coefficient of drainage area between 0.3 and 3:

    >>> area = rm.Parameter(lower=0.3, upper=3, opti=True)
    >>> corrections = rm.CorrectionParameters(area=area)
    >>> corrections.area.opti
    True
    """

    _computed_attributes = "area", "pet", "rainfall"
    _c_class = CCorrection
    area : Parameter = _DerivedTypeDecriptor(
        0, Parameter,
        doc="Factor correcting the drainage area of the watershed (-)."
    ) # type: ignore
    pet : Parameter = _DerivedTypeDecriptor(
        1, Parameter,
        doc="Potential Evapotranspiration correction factor (%)",
    ) # type: ignore
    rainfall : Parameter = _DerivedTypeDecriptor(
        2, Parameter,
        doc="Rainfall correction factor (%).",
    ) # type: ignore

    def __init__(
            self,
            area: ParameterType = None,
            pet: ParameterType = None,
            rainfall: ParameterType = None,
        ) -> None: 
        self._init_c()

        if area is not None:
            self.area = _build_parameter(area)
        if pet is not None:
            self.pet = _build_parameter(pet)
        if rainfall is not None:
            self.rainfall = _build_parameter(rainfall)