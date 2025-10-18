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
Watershed connection tree.
"""
from __future__ import annotations
from typing import Union, Optional, Dict, List

import numpy as np

from rameau.wrapper import CTree

from rameau.core import Watershed
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import wrap_property

WatershedType = Union[
    List[Union[dict, Watershed]], Dict[int, Union[Watershed, dict]]
]

class Tree(AbstractWrapper):
    """Watershed connection tree.

    Parameters
    ----------
    watersheds : `list` or `dict`
        If provided as a list, identifiers of each `Watershed` are deduced
        from their positions in the list, starting from 1. If provided as a
        dictionary, keys correspond to the user-defined identifiers.
        Identifiers needs to be consistent with the ones provided for the
        ``connection`` keyword.

    connection : `dict`, optional
        Dictionary of key/value integer pairs representing a watershed
        identifier starting from 1. Dictionary elements describe the connection
        between upstream watersheds and downstream watersheds. A 0 downstream
        value means that the corresponding upstream watershed is the watershed
        outlet.
    
    Returns
    -------
    `Tree`
        
    Examples
    --------
    Creation of three watersheds with default dummy parameters:

    >>> b1 = rm.Watershed()
    >>> b2 = rm.Watershed()
    >>> b3 = rm.Watershed()

    Creation of a watershed connection tree. Here b1 is connected to b3, b2 to
    b3, and b3 is the watershed outlet.

    >>> t = rm.Tree(watersheds=[b1, b2, b3], connection={1: 3, 2: 3, 3: 0})
    >>> for w in t.watersheds:
    ...     print(f"Watershed {w.id}: {w.strahler_order}")
    Watershed 1: 1
    Watershed 2: 1
    Watershed 3: 2

    The ``watersheds`` keyword argument can be a dictionary with user-defined
    identifiers.

    >>> t = rm.Tree(
    ...     watersheds={9: b1, 1: b2, 2: b3}, connection={9: 2, 1: 2, 2: 0}
    ... )
    >>> for w in t.watersheds:
    ...     print(f"Watershed {w.id}: {w.strahler_order}")
    Watershed 1: 1
    Watershed 2: 2
    Watershed 9: 1
    """

    _computed_attributes =  "watersheds", "connection"  # Order matters
    _c_class = CTree

    def __init__(
        self,
        watersheds: WatershedType,
        connection: Optional[Dict[int, int]] = None
    ) -> None: 
        self._init_c()

        if len(watersheds) == 1 and connection is None:
            connection = {1:0}
        elif len(watersheds) > 1 and connection is None:
            raise ValueError("Missing connection keyword argument")

        self.watersheds = watersheds
        self.connection = connection
    
    @staticmethod
    def from_csv(
        path: str,
        watersheds: WatershedType
    ) -> Tree:
        """Import connections between upstream and downstream watersheds from a
        CSV file. The CSV file must contain two columns of integer values, with
        a header line at the beginning of the file.
        
        Parameters
        ----------
        path : `str`
            Path to CSV file.
        watersheds : `list` or `dict`
            `Watershed` for this watershed connection tree. If provided as a
            list, ids of each watershed are deduced from their positions in the
            list, starting from 1. If provided as a dictionary, keys correspond
            to the ids of the watersheds and values either to `Watershed` object
            or `dict`. Keys needs to be consistent with the ``connection``
            keyword.
        
        Returns
        -------
        `Tree`

        Examples
        --------
        The content of an example of connection tree CSV file for three
        watersheds is shown below::

            Watershed Downstream
            1 3
            2 3
            3 0
        
        Assuming this content is written in the :file:`data/connection.csv`
        file, building a tree is done with:

        >>> wds = [rm.Watershed() for i in range(3)]
        >>> t = rm.Tree.from_csv(path="data/connection.csv", watersheds=wds)
        >>> for w in t.watersheds:
        ...     print(f"Watershed {w.id}: {w.strahler_order}")
        Watershed 1: 1
        Watershed 2: 1
        Watershed 3: 2
        """
        data = np.loadtxt(path, skiprows=1, dtype=int)
        connection = {row[0]:row[1] for row in data}
        return Tree(watersheds=watersheds, connection=connection)
    
    def to_csv(self, path: str) -> None:
        """Export a watershed connection dictionary to a CSV file.

        Parameters
        ----------
        path : `str`
            File path of CSV file to export.
        """
        header = "Watershed Downstream\n"
        with open(path, 'w') as f:
            f.write(header)
            data = np.array(
                [[key, value] for key, value in self.connection.items()]
            )
            np.savetxt(f, data, fmt='%d')
    
    @property
    def connection(self) -> dict:
        """Dictionary of key/value integer pairs representing a watershed
        identifier starting from 1.

        Returns
        -------
        `dict`
        """
        data = self._m.getConnection()
        return {row[1]:row[2] for row in data.T}
    
    @connection.setter
    def connection(self, v: dict) -> None:
        ids = np.empty((3, len(v)))
        keys = list(v.keys())
        keys.sort()
        for i, key in enumerate(keys):
            ids[0, i] = i + 1
            ids[1, i] = key
            ids[2, i] = v[key]
        ids = np.asfortranarray(ids)
        self._m.setConnection(ids)

    @property
    def watersheds(self) -> List[Watershed]:
        """List of `Watershed`. If this attribute is set directly
        without passing by the `Tree` constructor, connection is reset
        and all watersheds considered as disconnected. You need to
        set again the `connection` attribute.

        Returns
        -------
        `list`
        """
        return [self._ctopy_bas(bas) for bas in self._m.getVectorWatershed(0)]

    @wrap_property(Watershed)
    def _ctopy_bas(self, __watershed):
        return __watershed
    
    @watersheds.setter
    def watersheds(self, watersheds: WatershedType) -> None:
        if isinstance(watersheds, list):
            if not bool(watersheds):
                raise ValueError("Empty list not allowed")
        elif isinstance(watersheds, dict):
            if not watersheds.keys():
                raise ValueError("Empty dict not allowed")
            keys = list(watersheds.keys())
            keys.sort()
            watersheds = [watersheds[key] for key in watersheds.keys()]
        else:
            raise TypeError(f"{type(watersheds)} type not allowed.")
        watersheds2 = [
            Watershed(**b) if isinstance(b, dict) else b for b in watersheds
        ]
        for i, wat in enumerate(watersheds2):
            if not wat.name.strip():
                wat.name = f"Watershed {i+1}"
        self._m.setVectorWatershed([b._m for b in watersheds2], 0)
    