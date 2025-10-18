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
Pumping parameters.
"""

from typing import Union, Optional

from rameau.wrapper import CPumping

from rameau.core.pumping import PumpingReservoir
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _DerivedTypeDecriptor

from rameau.core._utils import _build_type

class Pumping(AbstractWrapper):
    """Pumping parameters.
    
    Parameters
    ----------
    river: `dict` or `PumpingReservoir`, optional

    groundwater: `dict` or `PumpingReservoir`, optional

    """

    _computed_attributes = ("river", "groundwater")
    _c_class = CPumping
    groundwater: PumpingReservoir = _DerivedTypeDecriptor(0, PumpingReservoir) #type: ignore
    river: PumpingReservoir = _DerivedTypeDecriptor(1, PumpingReservoir) #type: ignore

    def __init__(
        self,
        river: Optional[Union[dict, PumpingReservoir]] = None,
        groundwater: Optional[Union[dict, PumpingReservoir]] = None,
    ) -> None: 
        self._init_c()

        if river is not None:
            self.river = _build_type(river, PumpingReservoir)
        if groundwater is not None:
            self.groundwater = _build_type(groundwater, PumpingReservoir)