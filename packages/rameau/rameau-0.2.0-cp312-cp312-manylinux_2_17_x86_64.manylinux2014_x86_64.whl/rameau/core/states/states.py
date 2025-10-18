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
Model states.
"""

from __future__ import annotations
from typing import List
from rameau.wrapper import CStates
from rameau.core._descriptor import _FloatDescriptor, _VectorDescriptor

from rameau.core._abstract_wrapper import AbstractWrapper

class States(AbstractWrapper):
    """Model states.

    Parameters
    ----------
    h_thornthwaite: `float`, optional
        Water level (mm) in the soil reservoir using the Thornthwaite method.
        See `ThornthwaiteReservoir` for details.

    h_progressive: `float`, optional
        Water level (mm) in the soil reservoir using the GR3J method.
        See `ProgressiveReservoir` for details.

    h_transfer: `float`, optional
        Water level (mm) in the transfer reservoir.
        See `TransferReservoir` for details.

    h_snow: `float`, optional
        Snow water equivalent (mm) of the snow pack.
        See `SnowReservoir` for details.

    h_pump_riv: `float`, optional

    h_pump_gw: `float`, optional

    h_infl_gw: `List`, optional

    gm_pump_riv: `float`, optional

    gm_pump_gw: `float`, optional

    gm_infl_gw: `List`, optional

    r_snow: `float`, optional
        Water retention (-) in the snow pack.
        See `SnowReservoir` for details.

    h_groundwater: `List`, optional
        Water level (mm) in the groundwater reservoirs.
        See `Groundwater` for details.
    
    q_local: `List`, optional
        Total water level (mm) produced locally. 

    q_outlet: `List`, optional
        Historical riverflow (:math:`m^{3}.s^{-1}`) produced at the
        watershed outlet.
    
    Returns
    -------
    `States`
    """
    _computed_attributes = (
        "h_thornthwaite", "h_progressive", "h_transfer",
        "h_snow", "r_snow", "h_groundwater",
        "h_pump_riv", "h_pump_gw", "gm_pump_riv", "gm_pump_gw",
        "q_local", "q_outlet", "h_infl_gw", "gm_infl_gw"
    )
    _c_class = CStates
    h_thornthwaite: float = _FloatDescriptor(0) #type: ignore
    h_progressive: float  = _FloatDescriptor(1) #type: ignore
    h_transfer: float  = _FloatDescriptor(2) #type: ignore
    h_snow: float  = _FloatDescriptor(3) #type: ignore
    r_snow: float  = _FloatDescriptor(4) #type: ignore
    h_pump_riv: float  = _FloatDescriptor(5) #type: ignore
    h_pump_gw: float  = _FloatDescriptor(6) #type: ignore
    gm_pump_riv: float  = _FloatDescriptor(7) #type: ignore
    gm_pump_gw: float  = _FloatDescriptor(8) #type: ignore
    h_groundwater: List[float] = _VectorDescriptor(0, float) #type: ignore
    q_local: List[float] = _VectorDescriptor(1, float) #type: ignore
    q_outlet: List[float] = _VectorDescriptor(2, float) #type: ignore
    h_infl_gw: List[float] = _VectorDescriptor(3, float) #type: ignore
    gm_infl_gw: List[float] = _VectorDescriptor(4, float) #type: ignore

    def __init__(
        self,
        h_thornthwaite: float = 0.0,
        h_progressive: float = 0.0,
        h_transfer: float = 0.0,
        h_snow: float = 0.0,
        r_snow: float = 0.0,
        h_pump_riv: float = 0.0,
        h_pump_gw: float = 0.0,
        h_infl_gw: List[float] = [],
        gm_pump_riv: float = 0.0,
        gm_pump_gw: float = 0.0,
        gm_infl_gw: List[float] = [],
        h_groundwater: List[float] = [0.0],
        q_local: List[float] = [0.0, 0.0],
        q_outlet: List[float] = [0.0, 0.0]
    ) -> None: 
        self._init_c()

        self.h_thornthwaite = h_thornthwaite
        self.h_progressive = h_progressive
        self.h_transfer = h_transfer
        self.h_snow = h_snow
        self.r_snow = r_snow
        self.h_pump_riv = h_pump_riv
        self.h_pump_gw = h_pump_gw
        self.h_infl_gw = h_infl_gw
        self.gm_pump_riv = gm_pump_riv
        self.gm_pump_gw = gm_pump_gw
        self.gm_infl_gw = gm_infl_gw
        self.h_groundwater = h_groundwater
        self.q_local = q_local
        self.q_outlet = q_outlet