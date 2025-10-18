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
Snow reservoir.
"""

from typing import Union, Optional

from rameau.wrapper import CSnowReservoir

from rameau.core.parameter import Parameter
from rameau.core.snow import DegreeDayParameters, SnowCorrectionParameters
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._descriptor import _FloatDescriptor, _DerivedTypeDecriptor

from rameau._typing import ParameterType
from rameau.core._utils import _build_type,  _build_parameter

class SnowReservoir(AbstractWrapper):
    """Snow reservoir.
    
    Parameters
    ----------
    melting : `dict` or `Parameter`, optional
        |SWE| likely to melt daily from caloris of the soil (1/10
        mm/day).

    retention : `dict` or `Parameter`, optional
        Maximum water retention of the snowpack (%).

    degree_day : `dict` or `DegreeDayParameters`, optional
        Degree day model parameters.

    snow_correction : `dict` or `SnowCorrectionParameters`, optional
        Correction terms of meteorological inputs applied during the snow
        melting physical processes.

    swe : `float`
        Snow water equivalent (mm).

    r : `float`
        Water retention (%).

    Returns
    -------
    `SnowReservoir`

    Examples
    --------
    We create a snow reservoir:

    >>> s = rm.snow.SnowReservoir(
    ...     degree_day=dict(temperature=0.1, coefficient=4),
    ...     retention=5,
    ...     melting=5,
    ...     snow_correction=dict(temperature=0.5),
    ...     swe=2
    ... )
    >>> s.swe
    2.0
    >>> s.production(rainfall=5, pet=2, temperature=-2)
    {'snow_melt_to_soil': 0.5,
     'snow_melt': 0.0,
     'runoff': 0.0,
     'aet': 2.0,
     'upet': 0.0}
    >>> s.swe
    4.5
    """

    _computed_attributes = (
        "melting", "retention", "degree_day", "snow_correction", "swe", "r"
    )
    _c_class = CSnowReservoir
    swe: float = _FloatDescriptor(
        0, "Snow water equivalent (mm)."
    ) #type: ignore
    r: float = _FloatDescriptor(
        1, "Water retention (%)"
    ) #type: ignore
    retention: Parameter = _DerivedTypeDecriptor(
        0, Parameter,
        "Maximum water retention of the snowpack (%)."
    ) #type: ignore
    melting: Parameter = _DerivedTypeDecriptor(
        1, Parameter,
        "|SWE| likely to melt daily from caloris of the soil (1/10 mm/day)."
    ) #type: ignore
    degree_day: DegreeDayParameters = _DerivedTypeDecriptor(
        0, DegreeDayParameters,
        "Degree day model parameters."
    ) #type: ignore
    snow_correction: SnowCorrectionParameters = _DerivedTypeDecriptor(
        0, SnowCorrectionParameters,
        (
          "Correction terms of meteorological inputs applied during the snow "
          "melting physical processes."  
        )
    ) #type: ignore

    def __init__(
        self,
        melting: ParameterType = None,
        retention: ParameterType = None,
        degree_day: Optional[Union[dict, DegreeDayParameters]] = None,
        snow_correction: Optional[Union[dict, SnowCorrectionParameters]] = None,
        swe: float = 0,
        r: float = 0
    ) -> None: 
        self._init_c()

        if melting is not None:
            self.melting = _build_parameter(melting)
        if retention is not None:
            self.retention = _build_parameter(retention)
        if degree_day is not None:
            self.degree_day = _build_type(degree_day, DegreeDayParameters)
        if snow_correction is not None:
            self.snow_correction = _build_type(
                snow_correction, SnowCorrectionParameters
            )
        
        self.swe = swe
        self.r = r
    
    def production(
        self,
        rainfall:float,
        pet:float,
        temperature:float,
        snow:Optional[float] = None,
        deltat:float = 86400,
    ) -> dict:
        r"""Production function of the snow reservoir.

        Parameters
        ----------
        rainfall : `float`
            Rainfall data (mm).

        pet : `float`
            |PET| data (mm).

        temperature : `float`
            Temperature data (mm).

        snow : `float`, optional
            Snow data (mm).

        deltat : `float`, optional
            Time step length (s).
        
        Returns
        -------
        `dict`
            Output fluxes with keys:

            ``'snow_melt_to_soil'``
                Snow melting toward the soil (mm)
            ``'snow_melt'``
                Snow melting contributing to effective rainfall (mm)
            ``'runoff'``
                Snow runoff contributing to effective rainfall (mm)
            ``'aet'``
                |AET| (mm)
            ``'upet'``
                |UPET| (mm)
        """
        deltat = int(deltat)
        if snow is None:
            snow = 1e+20
        return self._m.production(rainfall, pet, snow, temperature, deltat)