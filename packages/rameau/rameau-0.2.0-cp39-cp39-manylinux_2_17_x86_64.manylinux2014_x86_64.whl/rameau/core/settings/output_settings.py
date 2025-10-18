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
Output settings.
"""

from rameau.wrapper import COutputSettings
from rameau.core._descriptor import _BoolDescriptor

from rameau.core._abstract_wrapper import AbstractWrapper

class OutputSettings(AbstractWrapper):
    """Output settings.

    Define which output files will be written 
    using `Simulation.write_outputs`.
    
    Parameters
    ----------
    budget: `bool`, optional
        Write budget csv files.

    metrics: `bool`, optional
        Write metrics csv files.

    parameters: `bool`, optional
        Write parameters csv files.

    states: `bool`, optional
        Write states csv files.

    toml: `bool`, optional
        Write toml parameter file.

    Returns
    -------
    `OutputSettings`
    """

    _computed_attributes = "budget", "metrics", "parameters", "states", "toml"
    _c_class = COutputSettings
    budget: bool = _BoolDescriptor(0) # type: ignore
    metrics: bool = _BoolDescriptor(1) # type: ignore
    parameters: bool = _BoolDescriptor(2) # type: ignore
    states: bool = _BoolDescriptor(3) # type: ignore
    toml: bool = _BoolDescriptor(4) # type: ignore

    def __init__(
            self,
            budget: bool = False,
            metrics: bool = True,
            parameters: bool = True,
            states: bool = True,
            toml: bool = True
        ) -> None: 
        self._init_c()

        self.budget = budget
        self.metrics = metrics
        self.parameters = parameters
        self.states = states
        self.toml = toml