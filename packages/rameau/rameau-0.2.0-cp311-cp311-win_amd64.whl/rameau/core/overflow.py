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
Overflow parameters.
"""

from typing import Literal

from rameau.wrapper import COverflow

from rameau.core import Parameter
from rameau.core._abstract_wrapper import AbstractWrapper

from rameau._typing import ParameterType
from rameau.core._utils import _build_parameter,  _check_literal
from rameau.core._descriptor import _DerivedTypeDecriptor, _StrDescriptor

class OverflowParameters(AbstractWrapper):
    """Overflow parameters.
    
    Parameters
    ----------
    halflife : `dict` or `Parameter`, optional
        Half-life parameter (time step).

    threshold : `dict` or `Parameter`, optional
        Overflow threshold (mm).

    loss : `str`, optional
        Fate of overflow (only for transfer reservoir).

            =================  =========================================
            loss               description
            =================  =========================================
            ``'no'``           Overflow is directly added to the river
                               flow.
            ``'loss'``         Overflow leaves the system.

            ``'groundwater'``  Overflow is added to the baseflow
                               component of the river flow.
            =================  =========================================
    
    Returns
    -------
    `OverflowParameters`
    """

    _computed_attributes = "halflife", "threshold", "loss"
    _c_class = COverflow
    threshold: Parameter = _DerivedTypeDecriptor(
        0, Parameter,
        doc="Overflow threshold (mm)."
     ) # type: ignore
    halflife: Parameter = _DerivedTypeDecriptor(
        1, Parameter,
        doc="Half-life parameter (time step)."
     ) # type: ignore
    loss: str = _StrDescriptor(
        0, doc="Fate of overflow (only for transfer reservoir)."
     ) # type: ignore

    def __init__(
        self,
        halflife: ParameterType = None,
        threshold: ParameterType = None,
        loss: Literal['no', 'groundwater', 'loss'] = 'no',
    ) -> None: 
        self._init_c()

        if halflife is not None:
            self.halflife = _build_parameter(halflife)
        if threshold is not None:
            self.threshold = _build_parameter(threshold)
        
        _check_literal(loss, ["no", "groundwater", "loss"])
        self.loss = loss