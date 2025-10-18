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
Degree day model parameters.
"""

from rameau.wrapper import CDegreeDay

from rameau.core import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter
from rameau.core._descriptor import _DerivedTypeDecriptor

class DegreeDayParameters(AbstractWrapper):
    """Degree day model parameters.
    
    Parameters
    ----------
    coefficient : `dict` or `Parameter`, optional
        Amount of melt that occurs per positive degree day
        (mm/°C/day)

    temperature : `dict` or `Parameter`, optional
        Temperature threshold above which all rainfall is assumed to fall
        as snow (°C).

    Returns
    -------
    `DegreeDayParameters`

    Examples
    --------
    >>> temperature = rm.Parameter(value=0.2)
    >>> coefficient = dict(value=2)
    >>> corrections = rm.snow.DegreeDayParameters(
    ...     temperature=temperature, coefficient=coefficient
    ... )
    >>> corrections.coefficient.value
    2.0
    """

    _computed_attributes = "coefficient", "temperature"
    _c_class = CDegreeDay
    temperature : Parameter = _DerivedTypeDecriptor(
        0, Parameter,
        doc="Temperature threshold above which all rainfall is assumed to fall as snow (°C)."
    ) # type: ignore
    coefficient : Parameter = _DerivedTypeDecriptor(
        1, Parameter,
        doc="Amount of melt that occurs per positive degree day (mm/°C/day)."
    ) # type: ignore

    def __init__(
            self,
            coefficient: ParameterType = None,
            temperature: ParameterType = None,
        ) -> None: 
        self._init_c()

        if coefficient is not None:
            self.coefficient = _build_parameter(coefficient)
        if temperature is not None:
            self.temperature = _build_parameter(temperature)