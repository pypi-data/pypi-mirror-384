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
Input.
"""

from __future__ import annotations
from typing import Optional

import datetime
import numpy as np
import pandas as pd

from rameau.wrapper import CInput, CDatetime_f

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import _get_datetime
from rameau.core._descriptor import _FloatDescriptor

class Input(AbstractWrapper):
    """Input wrapping data time series as a two-dimensional numpy array
    with the corresponding dates.
    
    Parameters
    ----------
    data: `numpy.ndarray`.
        Two-dimensional array containing the time series to store. Rows
        correspond to the dates and columns correspond to the number of
        input time series.

    dates: `pandas.DatetimeIndex`, optional.
        Dates of the time series. Default value corresponds to a daily
        `pandas.DatetimeIndex` starting from 1900-01-01.

    nodata: `float`, optional.
        Missing data value.
    
    Returns
    -------
    `Input`
    """
    _computed_attributes = "data", "dates", "nodata"
    _c_class = CInput
    nodata: float = _FloatDescriptor(0, "Missing data value.") #type: ignore

    def __init__(
        self,
        data: np.ndarray,
        dates: Optional[pd.DatetimeIndex] = None,
        nodata: float = 1e+20
    ) -> None: 
        self._init_c()

        self.nodata = float(nodata)
        self.data = data

        ntimestep = data.shape[0]
        if dates is None:
            dates = pd.date_range(
                "1900-1-1", periods=ntimestep, freq="D"
            )
        else:
            if not isinstance(dates, pd.DatetimeIndex):
                raise TypeError(f"Type {type(dates)} not allowed.")

        if dates.shape[0] != ntimestep:
            raise ValueError("Incoherent shapes between dates and data.")

        self.dates = dates

    @property
    def dates(self) -> pd.DatetimeIndex:
        """Dates of the time series.

        Returns
        -------
        `float`
        """
        dates = []
        for date_f in self._m.getVectorDates(0):
            dates.append(self._get_date(date_f.getDatetime()))
        return pd.DatetimeIndex(dates)
    
    @_get_datetime
    def _get_date(self, date) -> datetime.datetime:
        return date

    @dates.setter
    def dates(self, v: pd.DatetimeIndex) -> None:
        dates = []
        for date in v.to_pydatetime():
            a = CDatetime_f()
            a.setDatetime(self._set_dict_date(date))
            dates.append(a)
        self._m.setVectorDates(dates, 0)

    def _set_dict_date(self, v):
        return {
            "year":v.year, "month":v.month, "day":v.day,
            "hour":v.hour, "minute":v.minute, "second":v.second
        }

    @property
    def data(self) -> np.ndarray:
        """Two-dimensional array containing the time series to store.

        Returns
        -------
        `numpy.ndarray`
        """
        return self._m.getData()

    @data.setter
    def data(self, v: np.ndarray) -> None:
        v = np.where(np.isnan(v), self.nodata, v)
        if v.ndim == 1:
            v = v.reshape(-1, 1)
        self._m.setData(np.asfortranarray(v))
