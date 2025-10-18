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
Watershed.
"""
from typing import Union, Optional

from rameau.wrapper import CWatershed

from rameau.core import (
    RiverParameters, CorrectionParameters,
    ThornthwaiteReservoir, ProgressiveReservoir,
    TransferReservoir, Meteo, Influence
)
from rameau.core.snow import SnowReservoir
from rameau.core.pumping import Pumping
from rameau.core.groundwater import GroundwaterParameters
from rameau.core.forecast import ForecastCorrection
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import _build_type
from rameau.core._descriptor import (
    _DerivedTypeDecriptor,
    _BoolDescriptor,
    _StrDescriptor,
    _IntDescriptor
)

class Watershed(AbstractWrapper):
    """Watershed.
    
    Parameters
    ----------
    name: `str`, optional
        Watershed name.

    correction: `dict` or `CorrectionParameters`, optional
        Correction terms used when running a simulation.
        See `CorrectionParameters` for details.

    thornthwaite_reservoir: `dict` or `ThornthwaiteReservoir`, optional
        Soil reservoir using the Thornthwaite soil approach.
        See `ThornthwaiteReservoir` for details.

    progressive_reservoir: `dict` or `ProgressiveReservoir`, optional
        Soil reservoir using the GR3 soil approach.
        See `ProgressiveReservoir` for details.

    transfer_reservoir: `dict` or `TransferReservoir`, optional
        Transfer reservoir. See `TransferReservoir` for details.

    snow_reservoir: `dict` or `SnowReservoir`, optional
        Snow reservoir. See `SnowReservoir` for details.

    river: `dict` or `River`, optional
        River parameters. See `RiverParameters` for details.

    groundwater: `dict` or `GroundwaterParameters`, optional
        Groundwater parameters. See `GroundwaterParameters` for details.

    pumping: `dict` or `Pumping`, optional
        Pumping parameters. See `Pumping` for details.
    
    influence: `dict` or `Influence`, optional
        Influence parameters. See `Influence` for details.

    meteo: dict or `Meteo`, optional
        Parameters related to the meteorological inputs.
        See `Meteo` for details.

    forecast_correction: dict or `ForecastCorrection`, optional
        Forecast corrections. See `ForecastCorrection` for details.

    is_confluence: bool, optional
        True if the watershed is a confluence. Default to False.
    
    unit_time_step: bool, optional
        True for switching halflife time unit to time step instead of month.
        Default to False.

    Returns
    -------
    `Watershed`
    """

    _computed_attributes = (
        "name", "is_confluence", "unit_time_step", "river",
        "correction", "thornthwaite_reservoir",
        "progressive_reservoir", "transfer_reservoir",
        "snow_reservoir", "pumping", "groundwater",
        "meteo", "forecast_correction", "influence"
    )
    _c_class = CWatershed
    id: int = _IntDescriptor(0) #type: ignore
    strahler_order: int = _IntDescriptor(1) #type: ignore
    name: str = _StrDescriptor(0) #type: ignore
    forecast_correction: ForecastCorrection = _DerivedTypeDecriptor(
        0, ForecastCorrection
    ) #type: ignore
    river: RiverParameters = _DerivedTypeDecriptor(
        0, RiverParameters
    ) #type: ignore
    correction: CorrectionParameters = _DerivedTypeDecriptor(
        0, CorrectionParameters
    ) #type: ignore
    thornthwaite_reservoir: ThornthwaiteReservoir = _DerivedTypeDecriptor(
        0, ThornthwaiteReservoir
    ) #type: ignore
    progressive_reservoir: ProgressiveReservoir = _DerivedTypeDecriptor(
        0, ProgressiveReservoir
    ) #type: ignore
    transfer_reservoir: TransferReservoir = _DerivedTypeDecriptor(
        0, TransferReservoir
    ) #type: ignore
    snow_reservoir: SnowReservoir = _DerivedTypeDecriptor(
        0, SnowReservoir
    ) #type: ignore
    pumping: Pumping = _DerivedTypeDecriptor(
        0, Pumping
    ) #type: ignore
    influence: Influence = _DerivedTypeDecriptor(
        0, Influence
    ) #type: ignore
    groundwater: GroundwaterParameters = _DerivedTypeDecriptor(
        0, GroundwaterParameters
    ) #type: ignore
    meteo: Meteo = _DerivedTypeDecriptor(
        0, Meteo
    ) #type: ignore
    is_confluence: bool = _BoolDescriptor(0) #type: ignore
    unit_time_step: bool = _BoolDescriptor(1) #type: ignore

    def __init__(
        self,
        name: str = '',
        correction: Optional[Union[dict, CorrectionParameters]] = None,
        thornthwaite_reservoir: Optional[Union[dict, ThornthwaiteReservoir]] = None,
        progressive_reservoir: Optional[Union[dict, ProgressiveReservoir]] = None,
        transfer_reservoir: Optional[Union[dict, TransferReservoir]] = None,
        snow_reservoir: Optional[Union[dict, SnowReservoir]] = None,
        river: Optional[Union[dict, RiverParameters]] = None,
        groundwater: Optional[Union[dict, GroundwaterParameters]] = None,
        pumping: Optional[Union[dict, Pumping]] = None,
        influence: Optional[Union[dict, Influence]] = None,
        meteo: Optional[Union[dict, Meteo]] = None,
        forecast_correction: Optional[Union[dict, ForecastCorrection]] = None,
        is_confluence: bool = False,
        unit_time_step: bool = False,
    ) -> None: 
        self._init_c()

        self.name = name
        self.is_confluence = is_confluence
        self.unit_time_step = unit_time_step

        if river:
            self.river = _build_type(river, RiverParameters)
        if correction:
            self.correction = _build_type(correction, CorrectionParameters)
        if thornthwaite_reservoir:
            self.thornthwaite_reservoir = _build_type(
                thornthwaite_reservoir, ThornthwaiteReservoir
            )
        if progressive_reservoir:
            self.progressive_reservoir = _build_type(
                progressive_reservoir, ProgressiveReservoir
            )
        if transfer_reservoir:
            self.transfer_reservoir = _build_type(
                transfer_reservoir, TransferReservoir
            )
        if snow_reservoir:
            self.snow_reservoir = _build_type(
                snow_reservoir, SnowReservoir
            )
        if pumping:
            self.pumping = _build_type(pumping, Pumping)
        if influence:
            self.influence = _build_type(influence, Influence)
        if groundwater:
            self.groundwater = _build_type(
                groundwater, GroundwaterParameters
            )
        else:
            self.groundwater = GroundwaterParameters()
        if meteo:
            self.meteo = _build_type(meteo, Meteo)
        if forecast_correction:
            self.forecast_correction = _build_type(
                forecast_correction, ForecastCorrection
            )
        else:
            self.forecast_correction = ForecastCorrection()