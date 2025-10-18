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
Soil reservoir using the GR3 model :cite:p:`1989:edijatno_model`.
"""

from __future__ import annotations

from rameau.wrapper import CProgressiveReservoir

from rameau.core import Parameter

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter
from rameau.core._descriptor import (
    _BoolDescriptor,
    _FloatDescriptor,
    _DerivedTypeDecriptor
)

class ProgressiveReservoir(AbstractWrapper):
    """Soil reservoir using the GR3 approach :cite:p:`1989:edijatno_model`.
    
    Parameters
    ----------
    capacity : `dict` or `Parameter`, optional
        Soil water holding capacity (mm).

    pet_decrease : `bool`, optional
        Whether |PET| decreases when soil water content is lower than 50%.

    h : `float`, optional
        Soil moisture storage of the reservoir (mm). It is
        the reservoir level. Default is 0 mm.

    Returns
    -------
    `ProgressiveReservoir`

    Example
    -------
    In the API, soil reservoirs using the GR3 approach are created as follows:

    >>> sw = rm.ProgressiveReservoir(capacity=150.0, h=100)
    >>> sw.h
    100.0

    Now we introduce 150 mm of rainfall and 10 mm of |PET| and we produce
    effective rainfall and |AET|:
    >>> sw.production(150, 10)
    {'effective_rainfall':30.178375244140625, 'aet':10.0, 'unsatisfied_pet':0.0}

    Look how the reservoir level h has changed:
    >>> sw.h
    109.82162475585938
    """

    _computed_attributes = "capacity", "pet_decrease", "h"
    _c_class = CProgressiveReservoir
    h: float = _FloatDescriptor(0, "Soil water content (mm)") #type: ignore
    capacity: Parameter = _DerivedTypeDecriptor(
        0, Parameter,
        "Soil water holding capacity (mm)"
    ) #type: ignore
    pet_decrease: bool = _BoolDescriptor(
        0, "Whether Potential Evapotranspiration decreases when "
        "soil water content is lower than 50%."
    ) #type: ignore

    def __init__(
        self,
        capacity: ParameterType = None,
        pet_decrease: bool = False,
        h: float = 0.0
    ) -> None: 
        self._init_c()

        if capacity is not None:
            self.capacity = _build_parameter(capacity)

        self.pet_decrease = pet_decrease
        self.h = h

    def production(self, rainfall:float, pet:float) -> dict:
        r"""Production function of the soil reservoir using
        the GR3 approach :cite:p:`1989:edijatno_model`.

        Parameters
        ----------
        rainfall : `float`
            Rainfall (mm).
        
        pet : `float`
            |PET| (mm).

        Returns
        -------
        `dict`
            Output fluxes with keys:

            ``'effective_rainfall'``
                Effective rainfall (mm).
            ``'aet'``
                |AET| (mm).
            ``'unsatisfied_pet'``
                |UPET| (mm).
        """
        return self._m.production(rainfall, pet)