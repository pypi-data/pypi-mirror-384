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
File paths.
"""
from typing import Sequence
from rameau.wrapper import CFiles, CArrayString

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _StrDescriptor

class FilePaths(AbstractWrapper):
    """File paths.
    
    Parameters
    ----------
    rainfall : `str`, optional
        Path to rainfall data file.

    pet : `str`, optional
        Path to |PET| data file.

    temperature : `str`, optional
        Path to temperature data file.

    snow : `str`, optional
        Path to snow data file.

    riverobs : `str`, optional
        Path to river flow observation data file.

    groundwaterobs : `str`, optional
        Path to groundwater level observation data file.

    riverpumping : `str`, optional
        Path to river pumping data file.

    groundwaterpumping : `str`, optional
        Path to groundwater pumping data file.

    tree : `str`, optional
        Path to tree connection CSV file.

    states : `str`, optional
        Path to model states file.
    
    groundwaterinfluences : list, optional
        List of paths to groundwater level influence data files.

    Returns
    -------
    `FilePaths`
    """

    _computed_attributes = (
        "rainfall", "pet", "temperature",
        "snow", "riverobs", "riverpumping",
        "groundwaterobs", "groundwaterpumping",
        "tree", "states", "groundwaterinfluences"
    )
    _c_class = CFiles
    rainfall: str = _StrDescriptor(0) # type: ignore
    pet: str = _StrDescriptor(1) # type: ignore
    snow: str = _StrDescriptor(2) # type: ignore
    temperature: str = _StrDescriptor(3) # type: ignore
    tree: str = _StrDescriptor(4) # type: ignore
    riverobs: str = _StrDescriptor(5) # type: ignore
    riverpumping: str = _StrDescriptor(6) # type: ignore
    groundwaterobs: str = _StrDescriptor(7) # type: ignore
    groundwaterpumping: str = _StrDescriptor(8) # type: ignore
    states: str = _StrDescriptor(9) # type: ignore

    def __init__(
        self,
        rainfall: str = '',
        pet: str = '',
        temperature: str = '',
        snow: str = '',
        riverobs: str = '',
        riverpumping: str = '',
        groundwaterobs: str ='',
        groundwaterpumping: str = '',
        tree: str = '',
        states: str = '',
        groundwaterinfluences: Sequence[str] = []
    ) -> None: 
        self._init_c()

        self.rainfall = rainfall
        self.pet = pet
        self.snow = snow
        self.temperature = temperature
        self.tree = tree
        self.riverobs = riverobs
        self.riverpumping = riverpumping
        self.groundwaterobs = groundwaterobs
        self.groundwaterpumping = groundwaterpumping
        self.states = states
        self.groundwaterinfluences = groundwaterinfluences
    
    @property
    def groundwaterinfluences(self) -> Sequence[str]:
        data = self._m.getVectorArrayString(0)
        return [v.getString(0) for v in data]

    @groundwaterinfluences.setter
    def groundwaterinfluences(self, v: Sequence[str]) -> None:
        data = []
        for val in v:
            a = CArrayString()
            a.setString(val, 0)
            data.append(a)
        self._m.setVectorArrayString(data, 0)