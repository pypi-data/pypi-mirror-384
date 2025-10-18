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
Storage parameters.
"""

from rameau.wrapper import CStorage

from rameau.core.parameter import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter
from rameau.core._descriptor import _BoolDescriptor, _DerivedTypeDecriptor

class StorageParameters(AbstractWrapper):
    """Storage parameters.
    
    Parameters
    ----------
    coefficient : `dict` or `Parameter`, optional
        Storage coefficient (%).

    regression: `bool`, optional
        If True, storage coefficient will be optimised by regression.
        If False it will be optimised by a bounded optimisation method.
    
    Returns
    -------
    `StorageParameters`
    """
    _computed_attributes = "coefficient", "regression"
    _c_class = CStorage
    coefficient: Parameter = _DerivedTypeDecriptor(
        0, Parameter,
    ) # type: ignore
    regression: bool = _BoolDescriptor(0)# type: ignore

    def __init__(
        self,
        coefficient: ParameterType = None,
        regression=False
    ) -> None: 
        self._init_c()

        if coefficient is not None:
            self.coefficient = _build_parameter(coefficient)
        
        self.regression = regression