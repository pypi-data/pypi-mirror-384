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
Forecast settings.
"""

from __future__ import annotations
from typing import Optional, Literal, Union, List

import datetime

from rameau.wrapper import CForecastSettings

from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import _check_literal, _set_datetime, _get_datetime
from rameau.core._descriptor import (
     _BoolDescriptor, _VectorDescriptor,
     _DatetimeDescriptor, _TimedeltaDescriptor,
     _StrDescriptor
)

class ForecastSettings(AbstractWrapper):
    """
    Forecast settings.
    
    Parameters
    ----------
    emission_date: `datetime.datetime`, optional
        The date and time on which to issue a forecast.

    scope: `datetime.timedelta`, optional
        The duration for which to run the forecast. If not provided,
        set to one day.

    year_members: `list` or `ìnt`, optional
        The years to consider to form the forecast ensemble members.
        If not provided, all years in record are considered.

    correction: `str`, optional
        The approach to use to correct the initial conditions
        before issuing the forecast.

        =================  =========================================
        correction         description
        =================  =========================================
        ``'no'``           No correction is performed. This is
                           the default behaviour.

        ``'halflife'``     A correction using the observation
                           of the forecast variable on the issue
                           date is applied and then the correction
                           is gradually dampened overtime based on
                           a half-life parameter.
        =================  =========================================

    pumping_date: `datetime.datetime`, optional
        The date and time on which to start pumping.

    quantiles_output: `bool`, optional
        Whether to reduce the forecast ensemble members to specific
        climatology quantiles. If not provided, all years in record
        or years specified via the ``year_members`` parameter are
        considered. The quantiles can be chosen via the ``quantiles``
        parameter.

    quantiles: `list` or `int`, optional
        The climatology percentiles to include in the forecast ensemble
        members. Only considered if ``quantiles_output`` is set to
        `True`. By default, the percentiles computed are 10, 20, 50,
        80, and 90.

    norain: `bool`, optional
        Whether to include an extra ensemble member corresponding to
        a completely rain-free year. By default, this member is not
        included in the forecast output.
    
    Returns
    -------
    `ForecastSettings`
    """

    _computed_attributes = (
        "emission_date", "scope", "year_members", "correction", "pumping_date",
        "quantiles_output", "quantiles", "norain"
    )
    _c_class = CForecastSettings
    emission_date: datetime.datetime = _DatetimeDescriptor(
        0, doc="The date and time on which to issue a forecast."
    ) #type: ignore
    pumping_date: datetime.datetime = _DatetimeDescriptor(
        1, doc="The date and time on which to start pumping."
    ) #type: ignore
    scope: datetime.timedelta = _TimedeltaDescriptor(
        0, doc="The duration for which to run the forecast."
    ) #type: ignore
    year_members: Union[List[int], tuple[int]] = _VectorDescriptor(
        0, int, doc="The years to consider to form the forecast ensemble members."
    ) #type: ignore
    quantiles: Union[List[int], tuple[int]] = _VectorDescriptor(
        1, int, doc=(
            "The climatology percentiles to include in "
            "the forecast ensemble members."
        )
    ) #type: ignore
    quantiles_output: bool = _BoolDescriptor(
        0, doc=(
            "Whether to reduce the forecast ensemble members "
            "to specific climatology quantiles."
        )
    ) #type: ignore
    norain: bool = _BoolDescriptor(
        1, doc=(
            "Whether to include an extra ensemble member corresponding to"
            "a completely rain-free year."
        )
    ) #type: ignore
    correction: str = _StrDescriptor(
        0, doc=(
            "The approach to use to correct the initial conditions"
            "before issuing a forecast."
        )
    ) #type: ignore

    def __init__(
            self,
            emission_date: Optional[datetime.datetime] = None,
            scope: datetime.timedelta = datetime.timedelta(1),
            year_members: Optional[Union[List[int], tuple[int]]] = None,
            correction: Literal["no", "halflife", "enkf"] = "no",
            pumping_date: Optional[datetime.datetime] = None,
            quantiles_output: bool = False,
            quantiles: Union[List[int], tuple[int]] = [10, 20, 50, 80, 90],
            norain: bool = False
        ) -> None: 
        self._init_c()

        if emission_date is not None:
            self.emission_date = emission_date
        else:
            self.emission_date = datetime.datetime(9999, 12, 31)

        if pumping_date is not None:
            self.pumping_date = pumping_date
        else:
            self.pumping_date = datetime.datetime(9999, 12, 31)

        self.scope = scope

        _check_literal(
            correction, ["no", "halflife", "enkf"]
        )
        self.correction = correction

        if year_members is not None:
            if isinstance(year_members, (list, tuple)):
                self.year_members = year_members
            else:
                raise TypeError(f"Type {type(year_members)} not allowed.")

        self.quantiles_output = quantiles_output

        if isinstance(quantiles, (list, tuple)):
            self.quantiles = quantiles
        else:
            raise TypeError(f"Type {type(quantiles)} not allowed.")
        
        self.norain = norain