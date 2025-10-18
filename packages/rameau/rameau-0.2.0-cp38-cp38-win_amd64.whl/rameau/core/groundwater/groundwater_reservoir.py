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
Groundwater reservoir.
"""

from typing import Union, Optional

from rameau.wrapper import CGroundwaterReservoir

from rameau.core.parameter import Parameter
from rameau.core import OverflowParameters
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _DerivedTypeDecriptor, _FloatDescriptor

from rameau._typing import ParameterType
from rameau.core._utils import _build_type, _build_parameter

class GroundwaterReservoir(AbstractWrapper):
    """Groundwater reservoir.
    
    Parameters
    ----------
    halflife_baseflow: `dict` or `Parameter`, optional

    halflife_drainage: `dict` or `Parameter`, optional

    exchanges: `dict` or `Parameter`, optional

    overflow: `dict` or `OverflowParameters`, optional

    h: float, optional

    Returns
    -------
    `GroundwaterReservoir`
    """

    _computed_attributes = (
        "halflife_baseflow", "halflife_drainage", "exchanges", "overflow"
    )
    _c_class = CGroundwaterReservoir
    halflife_baseflow: Parameter = _DerivedTypeDecriptor(0, Parameter) # type: ignore
    halflife_drainage: Parameter = _DerivedTypeDecriptor(1, Parameter) # type: ignore
    exchanges: Parameter = _DerivedTypeDecriptor(2, Parameter) # type: ignore
    overflow: OverflowParameters = _DerivedTypeDecriptor(0, OverflowParameters) # type: ignore
    h: float = _FloatDescriptor(
        0, doc="Groundwater reservoir level (mm)."
    ) #type: ignore

    def __init__(
            self,
            halflife_baseflow: ParameterType = None,
            halflife_drainage: ParameterType = None,
            exchanges: ParameterType = None,
            overflow: Optional[Union[dict, OverflowParameters]] = None,
            h = 0
        ) -> None: 
        self._init_c()

        if halflife_baseflow is not None:
            self.halflife_baseflow = _build_parameter(halflife_baseflow)
        if halflife_drainage is not None:
            self.halflife_drainage = _build_parameter(halflife_drainage)
        if exchanges is not None:
            self.exchanges = _build_parameter(exchanges)
        if overflow is not None:
            self.overflow = _build_type(overflow, OverflowParameters)
        
        self.h = h
    
    def transfer(
            self,
            seepage: float,
            deltat: float = 86400
        ) -> dict:
        """Groundwater transfer function.

        Parameters
        ----------
        seepage : `float`
            Seepage (mm).
        deltat : `float`, optional
            Time step duration (s).

        Returns
        -------
        `dict`
            Output fluxes with keys:

            ``'baseflow'``
                River baseflow (mm).
            ``'drainage'``
                Drainage potentially flowing towards deeper groundwater reservoirs (mm).
            ``'overflow'``
                Overflow (mm).
            ``'unmet_pump'``
                Unsatisfied pumping (mm).
        """
        return self._m.transfer(seepage, int(deltat))