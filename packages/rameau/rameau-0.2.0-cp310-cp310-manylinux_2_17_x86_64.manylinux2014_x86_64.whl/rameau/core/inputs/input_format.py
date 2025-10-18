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
Input format.
"""
import datetime

from rameau.wrapper import CInputFormat

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import _set_datetime, _get_datetime
from rameau.core._descriptor import (
    _DatetimeDescriptor,
    _BoolDescriptor,
    _TimedeltaDescriptor
)

class InputFormat(AbstractWrapper):
    """Input format.
    
    Parameters
    ----------
    meteo_files: `bool`, optional
        Switch the text file format of the meteo input data. If true, a given
        meteorological input data (e.g. rainfall) is separated into multiple
        data text files. If false, the data are in the same CSV file. Default
        is False.

    starting_date: `datetime.datetime`, optional
        Starting date of the input data text files. Only used if the text files
        do not provide dates in the first column. This parameter sets the date
        of the first data record (first row of the file). Default is 1900-01-01.

    time_step: `datetime.timedelta`, optional
        Frequency of the input data text files. Only used if the text files do
        not provide dates in the first column. Associated to the `starting_date`
        parameter, it allows to set the dates of all the rows of the input
        files. Default is one day.
    
    Returns
    -------
    `InputFormat`
    """

    _computed_attributes = "meteo_files", "starting_date", "time_step"
    _c_class = CInputFormat
    meteo_files: bool = _BoolDescriptor(0, "Switch the text file format of the meteo input data.") #type: ignore
    starting_date: datetime.datetime = _DatetimeDescriptor(
        0, "Starting date of the input data text files."
    ) #type: ignore
    time_step: datetime.timedelta = _TimedeltaDescriptor(
        0, "Time step of the input data text files."
    ) #type: ignore

    def __init__(
        self,
        meteo_files: bool = False,
        starting_date: datetime.datetime = datetime.datetime(1900, 1, 1),
        time_step: datetime.timedelta = datetime.timedelta(days=0)
    ) -> None: 
        self._init_c()

        self.meteo_files = meteo_files
        self.starting_date = starting_date
        self.time_step = time_step