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
from typing import Optional, Union, Literal
from rameau.core import Parameter

ParameterType = Optional[Union[dict, Parameter]]
MethodType = Literal["all", "strahler", "independent"]
TransformationType = Literal["no", "square root", "inverse", "fifth root", "log"]
ObjFunctionType = Literal["nse", "kge", "kge_2012"]