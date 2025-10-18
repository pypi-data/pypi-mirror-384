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
from collections.abc import MutableMapping

class AbstractWrapper(MutableMapping):
    def _init_c(self):
        self._m = self._c_class() # type: ignore

    def __getitem__(self, __key):
        return getattr(self, __key)

    def __setitem__(self, __key, __value):
        if __key not in self._computed_attributes: # type: ignore
            raise KeyError(f'{__key} is not an attribute of {self}')
        setattr(self, __key, __value)

    def __delitem__(self, _):
        raise RuntimeError("Rameau parameters cannot be deleted.")
    
    def __iter__(self):
        for key in self._computed_attributes: # type: ignore
            yield key
    
    def __len__(self):
        return len(self._computed_attributes) # type: ignore

    # For pickling
    def __getstate__(self):
        return {key: getattr(self, key) for key in self._computed_attributes} # type: ignore
    
    # For pickling
    def __setstate__(self, state: dict):
        self._init_c()
        for key, value in state.items():
            setattr(self, key, value)