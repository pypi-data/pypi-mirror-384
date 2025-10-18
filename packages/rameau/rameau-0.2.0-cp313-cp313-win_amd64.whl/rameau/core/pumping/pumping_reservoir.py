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
Pumping reservoir.
"""

from rameau.wrapper import CPumpingReservoir

from rameau.core.parameter import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _DerivedTypeDecriptor

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter

class PumpingReservoir(AbstractWrapper):
    """Pumping reservoir.
    
    Parameters
    ----------
    coefficient: `dict` or `Parameter`, optional
        Fraction of the pumping rate that will be applied (-).

    halflife_rise: `dict` or `Parameter`, optional
        Halflife time of the falling pumping (time step).

    halflife_fall: `dict` or `Parameter`, optional
        Halflife time of the rising pumping (time step).

    Returns
    -------
    `PumpingReservoir`
    """

    _computed_attributes = "coefficient", "halflife_fall", "halflife_rise"
    _c_class = CPumpingReservoir
    halflife_rise: Parameter = _DerivedTypeDecriptor(0, Parameter) #type: ignore
    halflife_fall: Parameter = _DerivedTypeDecriptor(1, Parameter) #type: ignore
    coefficient: Parameter = _DerivedTypeDecriptor(2, Parameter) #type: ignore

    def __init__(
        self,
        coefficient: ParameterType = None,
        halflife_rise: ParameterType = None,
        halflife_fall: ParameterType = None
    ) -> None: 
        self._init_c()

        if coefficient is not None:
            self.coefficient = _build_parameter(coefficient)
        if halflife_fall is not None:
            self.halflife_fall = _build_parameter(halflife_fall)
        if halflife_rise is not None:
            self.halflife_rise = _build_parameter(halflife_rise)

    def budget(self, flow_in:float) -> dict:
        r"""Pumping reservoir budget.

        Parameters
        ----------
        flow_in : `float`
            Input flow of the reservoir.

        Returns
        -------
        `dict`
            Output fluxes with keys:

            ``'flow_out'``
                Output flow.
        """
        return self._m.budget(flow_in)