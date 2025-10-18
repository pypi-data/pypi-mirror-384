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

_doc_pattern = """{0}

Returns
-------
`{1}`
"""

class _AbstractDescriptor():
    def __init__(self, id, obj, doc=None) -> None:
        self._id = id
        if doc:
            self.__doc__ = _doc_pattern.format(doc, obj.__name__)


class _BoolDescriptor(_AbstractDescriptor):
    """
    Bool descriptor.
    """
    def __init__(self, id, doc=None) -> None:
        super().__init__(id, bool, doc=doc)

    def __get__(self, instance, type=None) -> bool:
        return instance._m.getBool(self._id)
    
    def __set__(self, instance, value) -> None:
        instance._m.setBool(value, self._id)


class _FloatDescriptor(_AbstractDescriptor):
    """
    Float descriptor.
    """
    def __init__(self, id, doc=None) -> None:
        super().__init__(id, float, doc=doc)

    def __get__(self, instance, type=None) -> float:
        return instance._m.getFloat(self._id)
    
    def __set__(self, instance, value) -> None:
        instance._m.setFloat(value, self._id)

class _IntDescriptor(_AbstractDescriptor):
    """
    Integer descriptor.
    """
    def __init__(self, id, doc=None) -> None:
        super().__init__(id, int, doc=doc)

    def __get__(self, instance, type=None) -> int:
        return instance._m.getInt(self._id)
    
    def __set__(self, instance, value) -> None:
        instance._m.setInt(value, self._id)

class _GetDerivedTypeDecriptor(_AbstractDescriptor):
    """
    Read only derived type descriptor
    """
    def __init__(self, id, obj, doc=None) -> None:
        super().__init__(id, obj, doc=doc)
        self._obj = obj

    def __get__(self, instance, type=None):
        b = self._obj.__new__(self._obj)
        meth = getattr(instance._m, f"get{self._obj.__name__}")
        b._m = meth(self._id)
        return b

class _DerivedTypeDecriptor(_GetDerivedTypeDecriptor):
    """
    Derived type descriptor.
    """
    def __set__(self, instance, value):
        meth = getattr(instance._m, f"set{self._obj.__name__}")
        meth(value._m, self._id)

class _StrDescriptor(_AbstractDescriptor):
    """
    Str descriptor.
    """
    def __init__(self, id, doc=None) -> None:
        super().__init__(id, str, doc=doc)

    def __get__(self, instance, type=None) -> str:
        return instance._m.getString(self._id)
    
    def __set__(self, instance, value) -> None:
        instance._m.setString(value, self._id)

class _TimedeltaDescriptor(_AbstractDescriptor):
    """
    Str descriptor.
    """
    def __init__(self, id, doc=None) -> None:
        super().__init__(id, datetime.timedelta, doc=doc)

    def __get__(self, instance, type=None) -> str:
        return instance._m.getTimedelta(self._id)
    
    def __set__(self, instance, value) -> None:
        instance._m.setTimedelta(value, self._id)


class _DatetimeDescriptor(_AbstractDescriptor):
    """
    Datetime descriptor.
    """
    def __init__(self, id, doc=None) -> None:
        super().__init__(id, datetime.datetime, doc=doc)

    def __get__(self, instance, type=None):
        val = instance._m.getDatetime(self._id)
        date = datetime.datetime(
            val["year"], val["month"], val["day"],
            val["hour"], val["minute"], val["second"]
        )

        if date == datetime.datetime(9999, 12 ,31):
            return
        return date
    
    def __set__(self, instance, value) -> None:
        if value == None:
            value = datetime.datetime(9999, 12 ,31)
        if not isinstance(value, datetime.datetime):
            raise TypeError(f"Type {type(value)} not allowed.")
        val = {
            "year":value.year, "month":value.month, "day":value.day,
            "hour":value.hour, "minute":value.minute, "second":value.second
        }
        instance._m.setDatetime(val, self._id)

class _VectorDescriptor(_AbstractDescriptor):
    """
    Vector descriptor.
    """
    def __init__(self, id, obj, doc=None) -> None:
        super().__init__(id, list, doc=doc)
        self._obj = obj

    def __get__(self, instance, type=None):
        if self._obj == int:
            return instance._m.getVectorInt(self._id)
        elif self._obj == float:
            return instance._m.getVectorFloat(self._id)
    
    def __set__(self, instance, value) -> None:
        if self._obj == int:
            instance._m.setVectorInt(value, self._id)
        elif self._obj == float:
            instance._m.setVectorFloat(value, self._id)

class _VectorDerivedTypeDescriptor(_AbstractDescriptor):
    """
    Derived Type Vector descriptor.
    """
    def __init__(self, id, obj, doc=None) -> None:
        super().__init__(id, obj, doc=doc)
        self._obj = obj

    def __get__(self, instance, type=None):
        meth = getattr(instance._m, f"getVector{self._obj.__name__}")
        val = []
        for res in meth(self._id):
            b = self._obj.__new__(self._obj)
            b._m = res
            val.append(b)
        return val
    
    def __set__(self, instance, value) -> None:
        meth = getattr(instance._m, f"setVector{self._obj.__name__}")
        meth([v._m for v in value], self._id)