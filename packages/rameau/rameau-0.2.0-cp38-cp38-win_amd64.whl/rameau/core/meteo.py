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
Collection of meteorological parameters.
"""

from __future__ import annotations
from typing import Union, Sequence

import numpy as np
from numpy.typing import NDArray

from rameau.wrapper import CMeteo

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _VectorDescriptor

class Meteo(AbstractWrapper):
    """Collection of meteorological parameters to calculate meteorological
    time series of a given watershed from given inputs.
    
    Parameters
    ----------
    columns: `list` or `numpy.ndarray`
        Column numbers of input files used to calculate meteorological time
        series. Index of column numbers starts from 1.

    weights: `list` or `numpy.ndarray`
        Weights to be applied to each meteorological time series corresponding
        to the column numbers of the ``columns`` keyword argument.
    
    Returns
    -------
    `Meteo`
    """

    _computed_attributes = "columns", "weights"
    _c_class = CMeteo
    columns: list = _VectorDescriptor(
        0, int, "Column numbers of meteorological input data text files."
    ) # type: ignore
    weights: list = _VectorDescriptor(
        0, float, "Weights to be applied to each meteorological time series."
    ) # type: ignore

    def __init__(
        self,
        columns: Sequence,
        weights: Sequence
    ) -> None: 
        self._init_c()

        if isinstance(columns, list):
            self.columns = list(map(int, columns))
        elif isinstance(columns, np.ndarray):
            self.columns = list(map(int, columns.tolist()))
        else:
            raise TypeError(f"Type {type(columns)} not allowed.")

        if isinstance(weights, list):
            self.weights = list(map(float, weights))
        elif isinstance(weights, np.ndarray):
            self.weights = list(map(float, weights.tolist()))
        else:
            raise TypeError(f"Type {type(weights)} not allowed.")
        
        if len(columns) != len(weights):
            raise ValueError("Inconsistent sizes between weights and column.")