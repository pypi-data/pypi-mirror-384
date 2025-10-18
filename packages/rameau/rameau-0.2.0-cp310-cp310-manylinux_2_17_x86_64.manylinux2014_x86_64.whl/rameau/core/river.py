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
Parameters for calculating and/or optimizing river flow in :math:`m^3.s^{-1}`.
"""
from __future__ import annotations
from typing import Union
import collections.abc

from rameau._typing import ParameterType
from rameau.wrapper import CRiver

from rameau.core.parameter import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import  _build_parameter
from rameau.core._descriptor import (
    _FloatDescriptor, _DerivedTypeDecriptor
)



class RiverParameters(AbstractWrapper):
    """Parameters for calculating and/or optimising river flow
    in :math:`m^3.s^{-1}`.
    
    Parameters
    ----------
    area : `dict` or `Parameter`, optional
        Watershed area (:math:`km^2`).

    exchange_riverflow : `dict` or `Parameter`, optional
        Minimum river flow always imposed in the river (:math:`m^3.s^{-1}`).

    concentration_time : `dict` or `Parameter`, optional
        Watershed concentration time (time steps).

    propagation_time : `dict` or `Parameter`, optional
        Watershed propagation time (time steps).

    weight : `float`, optional
        Weight given to river flow during the model optimization. A value
        of zero means no river flow optimisation.

    obslim : `[float, float]`, optional
        Bounds applied to the observed river flow during the model optimisation.

    Returns
    -------
    `RiverParameters`
    """

    _computed_attributes = (
        "area", "exchange_riverflow", "concentration_time",
        "propagation_time", "weight", "obslim"
    )
    _c_class = CRiver
    area_corr: float = _FloatDescriptor(0) #type: ignore
    area_cum: float = _FloatDescriptor(1) #type: ignore
    weight: float = _FloatDescriptor(2) #type: ignore
    area: Parameter = _DerivedTypeDecriptor(0, Parameter) #type: ignore
    exchange_riverflow: Parameter = _DerivedTypeDecriptor(1, Parameter) #type: ignore
    concentration_time: Parameter = _DerivedTypeDecriptor(2, Parameter) #type: ignore
    propagation_time: Parameter = _DerivedTypeDecriptor(3, Parameter) #type: ignore

    def __init__(
        self,
        area: ParameterType = None,
        exchange_riverflow: ParameterType = None,
        concentration_time: ParameterType = None,
        propagation_time: ParameterType = None,
        weight: float = 1.0,
        obslim: Union[list, tuple] = [0.0, 0.0]
    ) -> None: 
        self._init_c()

        if area is not None:
            self.area = _build_parameter(area)
        if exchange_riverflow is not None:
            self.exchange_riverflow = _build_parameter(exchange_riverflow)
        if concentration_time is not None:
            self.concentration_time = _build_parameter(concentration_time)
        if propagation_time is not None:
            self.propagation_time = _build_parameter(propagation_time)
        
        self.obslim = obslim
        self.weight = weight

    @property
    def obslim(self) -> list:
        return self._m.getVectorFloat(0)

    @obslim.setter
    def obslim(self, v: Union[list, tuple]) -> None:
        if isinstance(v, collections.abc.Sequence) and len(v) != 2:
            raise ValueError("Must be of size 2")

        self._m.setVectorFloat(v, 0)
