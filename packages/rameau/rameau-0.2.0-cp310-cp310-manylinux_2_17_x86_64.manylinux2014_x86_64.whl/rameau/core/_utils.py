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
import datetime
import functools
from typing import Any
from rameau.core import Parameter

# Decorator of getter property
# Convert C++ subclass in Python class
def wrap_property(cls):
    def decorator(func):
        @functools.wraps(func) # Needed for correct docstring in sphinx
        def factory(self, *args, **kwargs):
            b = cls.__new__(cls)
            b._m = func(self, *args, **kwargs)
            return b

        # inherit docstring
        factory.__doc__ = func.__doc__

        return factory
    return decorator

def _get_datetime(func):
    def factory(self, *args):
        v = func(self, *args)
        toto = datetime.datetime(
            v["year"], v["month"], v["day"],
            v["hour"], v["minute"], v["second"]
        )

        if toto == datetime.datetime(9999, 12 ,31):
            return
        return toto
    return factory

def _set_datetime(func):
    def factory(self, v):
        if v == None:
            v = datetime.datetime(9999, 12 ,31)
        _check_datetime(v)
        v2 = {
            "year":v.year, "month":v.month, "day":v.day,
            "hour":v.hour, "minute":v.minute, "second":v.second
        }
        func(self, v2)
    return factory

# rsetattr and rgetattr from :
# https://stackoverflow.com/questions/31174295/getattr-and-setattr-on-nested-subobjects-chained-properties/31174427#31174427
def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))

def _raise_type_error(var):
    raise TypeError(f"Type {type(var)} not allowed.")

def _build_parameter(var):
    if isinstance(var, float) or isinstance(var, int):
        return Parameter(value=var)
    else:
        return _build_type(var, Parameter)

def _build_type(var: Any, Partype: Any) -> Any:
    if isinstance(var, dict):
        return Partype(**var)
    elif isinstance(var, Partype):
        return var
    else:
        _raise_type_error(var)

def _check_literal(val, auths):
    if isinstance(val, str):
        if val not in auths:
            raise ValueError(f"Value {val} not allowed.")
    else:
        _raise_type_error(val)

def _check_datetime(val):
    if not isinstance(val, datetime.datetime):
        _raise_type_error(val)

def _check_bool(val):
    if not isinstance(val, bool):
        _raise_type_error(val)
        
def _check_str(val):
    if not isinstance(val, str):
        _raise_type_error(val)

def _check_scalar(val):
    if not isinstance(val, (int, float)):
        _raise_type_error(val)

def _check_timedelta(val):
    if not isinstance(val, datetime.timedelta):
        _raise_type_error(val)