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

from typing import Union, Sequence

from rameau.wrapper import CInfluence
from rameau.core.pumping import PumpingReservoir
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _VectorDerivedTypeDescriptor
from rameau.core._utils import _build_type

class Influence(AbstractWrapper):
    """Influence parameters.
    
    Parameters
    ----------
    groundwater: `dict` or `PumpingReservoir`, optional
    """
    _computed_attributes = "groundwater",
    _c_class = CInfluence
    groundwater: Sequence[PumpingReservoir] = _VectorDerivedTypeDescriptor(
        0, PumpingReservoir) #type: ignore

    def __init__(
        self,
        groundwater: Sequence[Union[dict, PumpingReservoir]] = [],
    ) -> None: 
        self._init_c()

        self.groundwater = [
            _build_type(res, PumpingReservoir)
            for res in groundwater
        ]