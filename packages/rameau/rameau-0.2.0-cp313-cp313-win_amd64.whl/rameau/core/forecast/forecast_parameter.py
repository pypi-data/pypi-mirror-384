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
Forecast correction parameters.
"""
import datetime

from rameau.wrapper import CForecastParameter

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _FloatDescriptor, _BoolDescriptor

class ForecastParameter(AbstractWrapper):
    """Forecast correction parameters.
    
    Parameters
    ----------
    halflife : `float`, optional
        Halflife value (time step).

    halflife_estimation : `bool`, optional
        Whether halflie value is estimated or not. Default to False.

    Returns
    -------
    `ForecastParameter`
    """

    _computed_attributes = 'halflife', 'halflife_estimation'
    _c_class = CForecastParameter
    halflife: float = _FloatDescriptor(0, doc="Halflife value (time step).") # type: ignore
    halflife_estimation: bool = _BoolDescriptor(
        0, "Whether halflie value is estimated or not"
    ) #type: ignore

    def __init__(
        self,
        halflife: float = 0.0,
        halflife_estimation: bool = False
    ) -> None: 
        self._init_c()
        self.halflife = float(halflife)
        self.halflife_estimation = halflife_estimation