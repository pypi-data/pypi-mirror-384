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
Soil reservoir using the Thornthwaite approach :cite:p:`1948:thornthwaite_approach`.
"""

from rameau.wrapper import CThornthwaiteReservoir

from rameau.core import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter
from rameau.core._descriptor import (
    _FloatDescriptor,
    _DerivedTypeDecriptor
)

class ThornthwaiteReservoir(AbstractWrapper):
    """Soil reservoir using the Thornthwaite approach
    :cite:p:`1948:thornthwaite_approach`.

    Parameters
    ----------
    capacity: `dict` or `Parameter`, optional
        Soil water holding capacity (mm). 

    h: `float`
        Soil water content of the reservoir (mm). It is
        the reservoir level. Default is 0 mm.

    Returns
    -------
    `ThornthwaiteReservoir`

    Examples
    --------
    Soil reservoirs using the Thornthwaite approach are created as follows:

    >>> sw = rm.ThornthwaiteReservoir(capacity=150.0, h=100)
    >>> sw.h
    100.0

    Now we introduce 150 mm of rainfall and 10 mm of |PET| and we produce
    effective rainfall and |AET|:
    >>> sw.production(150, 10)
    {'effective_rainfall':90.0, 'aet':10.0, 'unsatisfied_pet':0.0}

    Look how the reservoir level h has changed:
    >>> sw.h
    150.0
    """

    _computed_attributes = "capacity", "h"
    _c_class = CThornthwaiteReservoir
    h: float = _FloatDescriptor(0, "Soil water content (mm).") #type: ignore
    capacity: Parameter = _DerivedTypeDecriptor(
        0, Parameter, "Soil water holding capacity (mm)."
    ) #type: ignore

    def __init__(
        self,
        capacity: ParameterType = None,
        h: float = 0.0
    ) -> None: 
        self._init_c()

        if capacity is not None:
            self.capacity = _build_parameter(capacity)
        
        self.h = h
    
    def production(self, rainfall:float, pet:float) -> dict:
        r"""Production function of the soil reservoir using
        the Thornthwaite model :cite:p:`1948:thornthwaite_approach`.

        Parameters
        ----------
        rainfall: `float`
            Rainfall (mm).
        
        pet: `float`
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
