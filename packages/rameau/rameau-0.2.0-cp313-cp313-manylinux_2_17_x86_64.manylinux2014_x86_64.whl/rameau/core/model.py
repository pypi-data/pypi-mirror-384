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
rameau model.
"""
from __future__ import annotations
from typing import Union, Optional, Literal, List
import datetime
import functools

import pandas as pd
import numpy as np

from rameau.core.settings.spinup_settings import SpinupSettings
from rameau.wrapper import CModel # type: ignore

from rameau.core.settings import (
    SimulationSettings,
    ForecastSettings,
    OptimizationSettings,
    OutputSettings
)
from rameau.core.inputs import InputCollection
from rameau.core.states import StatesCollection, States
from rameau.core.tree import Tree
from rameau.core.simulation import (
    Simulation,
    OptiSimulation,
    ForecastSimulation
)

from rameau.core._utils import _check_literal
from rameau.core._abstract_wrapper import AbstractWrapper
from rameau.core._utils import _build_type, wrap_property
from rameau.core._descriptor import _DerivedTypeDecriptor

from rameau._typing import MethodType, TransformationType, ObjFunctionType

from copy import copy

def overload_sim(method):
    @functools.wraps(method)
    def factory(self, *args, **kwargs):
        sim = method(self, *args, **kwargs)
        sim._optimization_settings = copy(self.optimization_settings)
        sim._forecast_settings = copy(self.forecast_settings)
        return sim
    return factory

def overload_opti_sim(method):
    @functools.wraps(method)
    def factory(self, *args, **kwargs):
        sim = method(self, *args, **kwargs)
        sim._forecast_settings = copy(self.forecast_settings)
        return sim
    return factory

def overload_forecast_sim(method):
    @functools.wraps(method)
    def factory(self, *args, **kwargs):
        sim = method(self, *args, **kwargs)
        sim._optimization_settings = copy(self.optimization_settings)
        return sim
    return factory

class Model(AbstractWrapper):
    """Define a rameau model.
    
    Parameters
    ----------
    tree: `dict` or `Tree`
        Watershed connection tree.

    inputs: `dict` or `InputCollection`
        Model input data.

    init_states: `dict` or `StatesCollection`, optional
        Model initial states.

    simulation_settings: `dict` or `SimulationSettings`, optional
        Settings related to a simulation run.
        See `SimulationSettings` for details.

    optimization_settings: `dict` or `OptimizationSettings`, optional
        Settings related to an optimisation run.
        See `OptimizationSettings` for details.

    forecast_settings: `dict` or `ForecastSettings`, optional
        Settings related to a forecast run.
        See `ForecastSettings` for details.

    output_settings: `dict` or `OutputSettings`, optional
        Settings related to the simulation outputs
        See `OutputSettings` for details.
    
    Returns
    -------
    `Model`

    Examples
    --------
    Constructing model from `Tree` and `InputCollection`.

    >>> data = np.array([0.1, 0.2, 0.3])
    >>> model = rm.Model(
    ...     tree=rm.Tree(watersheds=[{}]),
    ...     inputs=rm.inputs.InputCollection(rainfall=data, pet=data)
    ... )
    >>> model.inputs.rainfall.data
    array([[0.1],
           [0.2],
           [0.3]], dtype=float32)

    Constructing model from `dict`.

    >>> model = rm.Model(
    ...     tree=dict(watersheds=[{}]),
    ...     inputs=dict(rainfall=data, pet=data)
    ... )
    >>> model.inputs.rainfall.data
    array([[0.1],
           [0.2],
           [0.3]], dtype=float32)
    """

    _computed_attributes = (
        "tree", "inputs", "init_states", "simulation_settings",
        "optimization_settings", "forecast_settings",
        "output_settings"
    )
    _c_class = CModel
    tree: Tree = _DerivedTypeDecriptor(
        0, Tree, "Watershed connection tree of the model."
    ) #type: ignore
    simulation_settings: SimulationSettings = _DerivedTypeDecriptor(
        0, SimulationSettings, "Settings related to a simulation run."
    ) #type: ignore
    optimization_settings: OptimizationSettings = _DerivedTypeDecriptor(
        0, OptimizationSettings, "Settings related to an optimization run."
    ) #type: ignore
    forecast_settings: ForecastSettings = _DerivedTypeDecriptor(
        0, ForecastSettings, "Settings related to an forecast run."
    ) #type: ignore
    output_settings: OutputSettings = _DerivedTypeDecriptor(
        0, OutputSettings, "Settings related to simulation outputs."
    ) #type: ignore
    init_states: StatesCollection = _DerivedTypeDecriptor(
        0, StatesCollection, "Model initial states."
    ) #type: ignore

    def __init__(
        self,
        tree: Union[dict, Tree],
        inputs: Union[dict, InputCollection],
        init_states: Optional[
            Union[List[Union[dict, States]], Union[dict, StatesCollection]]
        ] = None,
        simulation_settings: Optional[Union[dict, SimulationSettings]] = None,
        optimization_settings: Optional[Union[dict, OptimizationSettings]] = None,
        forecast_settings: Optional[Union[dict, ForecastSettings]] = None,
        output_settings: Optional[Union[dict, OutputSettings]] = None
    ) -> None: 
        self._init_c()

        self.tree = _build_type(tree, Tree)
        self.inputs = _build_type(inputs, InputCollection)
        if init_states is not None:
            if isinstance(init_states, list):
                self.init_states = StatesCollection(states=init_states)
            else:
                self.init_states = _build_type(init_states, StatesCollection)
        else:
            self._m.set_default_init_states()

        if simulation_settings is not None:
            self.simulation_settings = _build_type(
                simulation_settings, SimulationSettings
            )
        else:
            self.simulation_settings = SimulationSettings()

        if optimization_settings is not None:
            self.optimization_settings = _build_type(
                optimization_settings, OptimizationSettings
            )
        else:
            self.optimization_settings = OptimizationSettings()

        if forecast_settings is not None:
            self.forecast_settings = _build_type(
                forecast_settings, ForecastSettings
            )
        else:
            self.forecast_settings = ForecastSettings()

        if output_settings is not None:
            self.output_settings = _build_type(
                output_settings, OutputSettings
            )
        else:
            self.output_settings = OutputSettings()

    @overload_sim
    @wrap_property(Simulation)
    def create_simulation( self, **kwargs) -> Simulation:
        """Create a simulation.

        See `Model.create_simulation` for keyword argument descriptions.

        Returns
        -------
        `Simulation`
        """
        kwargs2 = {}
        for key in SimulationSettings._computed_attributes:
            if key in kwargs:
                kwargs2[key] = kwargs[key]
            else:
                kwargs2[key] = getattr(self.simulation_settings, key)
        opt = SimulationSettings(**kwargs2)
        sim, err = self._m.create_simulation(opt._m)
        if err.getInt(0) != 0:
            raise RuntimeError(err.getString(0))
        return sim
    
    @overload_sim
    @wrap_property(Simulation)
    def run_simulation(
        self,
        name: Optional[str] = None,
        starting_date: Optional[datetime.datetime] = None,
        spinup_settings: Optional[Union[SpinupSettings, dict]] = None
    ) -> Simulation:
        """Start a simulation run.

        Parameters
        ----------
        name: `str`, optional
            Name of the simulation. This name is used to name to the output
            directory. If omitted, default is "simulation".

        starting_date: `datetime.datetime`, optional
            Starting date of the simulation. This date needs to be contained in the
            rainfall input data. If None, default is the starting date of
            the rainfall input data. The simulation run will start from this
            date and will stop at the end of the meteorological input data.

        spinup_settings: `dict` or `SpinupSettings`, optional
            Spinup settings of the simulation. See `SpinupSettings` for details.

        Returns
        -------
        `Simulation`
        """
        attrs = {
            "name":name, "starting_date":starting_date,
            "spinup_settings":spinup_settings
        }
        kwargs = {}
        for key, value in attrs.items():
            if value is not None:
                kwargs[key] = value
            else:
                kwargs[key] = getattr(self.simulation_settings, key)
        opt = SimulationSettings(**kwargs)
        sim, err = self._m.run_simulation(opt._m)
        if err.getInt(0) != 0:
            raise RuntimeError(err.getString(0))
        return sim

    @overload_opti_sim
    @wrap_property(OptiSimulation)
    def run_optimization(
        self,
        maxit: Optional[int] = None,
        starting_date: Optional[datetime.datetime] = None,
        ending_date: Optional[datetime.datetime] = None,
        method: Optional[MethodType] = None,
        transformation: Optional[TransformationType] = None,
        river_objective_function: Optional[ObjFunctionType] = None,
        selected_watersheds: Optional[List[int]] = None,
        verbose = None
    ) -> OptiSimulation:
        """Start an optimisation run.

        Parameters
        ----------
        maxit: `int`, optional
            Number of iterations for the optimisation algorithm.

        starting_date: `datetime.datetime`, optional
            The date and time defining the start of the period to consider
            in the input data for the optimisation run.

        ending_date: `datetime.datetime`, optional
            The date and time defining the end of the period to consider
            in the input data for the optimisation run.

        method: `str`, optional
            The approach to use when several gauged watersheds need to
            be considered in the optimisation run.
            See `OptimizationSettings.method` for details.

        transformation: `str`, optional
            The function to apply to transform the observed and predicted river
            flow (Q) before computing the objective function.
            See `OptimizationSettings.transformation` for details.

        river_objective_function: `str`, optional
            The objective function to use to compare the observed and
            predicted river flow.
            See `OptimizationSettings.objective_function` for details.

        selected_watersheds: `list` or `int`, optional
            The indices of the watersheds to consider in the
            optimisation run. The indices relate to those in the
            sequence of watersheds specified in the `Tree`. If not
            provided, all gauged watersheds are considered.

        verbose: `bool`, optional
            Whether to display information for each step of the
            optimisation process. If not provided, no information is
            displayed.

        Returns
        -------
        `OptiSimulation`
        """
        attrs = {
            "maxit":maxit, "starting_date":starting_date,
            "ending_date":ending_date, "method":method,
            "transformation":transformation,
            "river_objective_function":river_objective_function,
            "selected_watersheds":selected_watersheds,
            "verbose":verbose
        }
        kwargs = {}
        for key, value in attrs.items():
            if value is not None:
                kwargs[key] = value
            else:
                val = getattr(self.optimization_settings, key)
                if not (key == 'selected_watersheds' and val == []):
                    kwargs[key] = val
        opt = OptimizationSettings(**kwargs)
        
        if opt.maxit > 0:
            sim, err = self._m.run_optimization(opt._m)
            if err.getInt(0) != 0:
                raise RuntimeError(err.getString(0))
            return sim
        else:
            raise RuntimeError("0 iterations defined (maxit=0).")

    @overload_forecast_sim
    @wrap_property(ForecastSimulation)
    def run_forecast(
        self,
        emission_date: Optional[datetime.datetime] = None,
        scope: Optional[datetime.timedelta] = None,
        year_members: Optional[Union[List[int], tuple[int]]] = None,
        correction: Optional[Literal["no", "halflife"]] = None,
        pumping_date: Optional[datetime.datetime] = None,
        quantiles_output: Optional[bool] = None,
        quantiles: Optional[Union[List[int], tuple[int]]] = None,
        norain: Optional[bool] = None
    ) -> ForecastSimulation:
        """Start a forecast run.

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
            before issuing a forecast. See `ForecastSettings` for details.

        pumping_date: `datetime.datetime`, optional

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
        `ForecastSimulation`
        """
        attrs = {
            "emission_date":emission_date, "scope":scope,
            "year_members":year_members,
            "correction":correction, "pumping_date":pumping_date,
            "quantiles_output":quantiles_output, "quantiles":quantiles,
            "norain":norain
        }
        kwargs = {}
        for key, value in attrs.items():
            if value is not None:
                kwargs[key] = value
            else:
                val = getattr(self.forecast_settings, key)
                if not (key == 'year_members' and val == []):
                    kwargs[key] = val
        fcast = ForecastSettings(**kwargs)
        sim, err = self._m.run_forecast(fcast._m)
        if err.getInt(0) != 0:
            raise RuntimeError(err.getString(0))
        return sim

    def get_input(
        self,
        variable: Literal[
            "rainfall", "pet", "snow", "temperature",
            "riverobs", "groundwaterobs",
            "riverpumping", "groundwaterpumping"
        ] = 'rainfall'
    ) -> pd.DataFrame:
        """Get model input data.

        Parameters
        ----------

        variable: `str`, optional
            The model input variable to retrieve.

            ======================== =======================================
            variable                 description
            ======================== =======================================
            ``'rainfall'``           The model input rainfall data.

            ``'pet'``                The model input |PET| data.

            ``'snow'``               The model input snow data.

            ``'temperature'``        The model input temperature data.

            ``'riverobs'``           The river flow observation data.

            ``'groundwaterobs'``     The groundwater level observation data.

            ``'riverpumping'``       The river pumping data.

            ``'groundwaterpumping'`` The Groundwater pumping data.
            ======================== =======================================

        Returns
        -------
        `pandas.DataFrame`
        """
        _check_literal(
            variable,
            [
                "rainfall", "pet", "snow", "temperature",
                "riverobs", "groundwaterobs",
                "riverpumping", "groundwaterpumping"
            ]
        )
        return self._input_to_dataframe(
            getattr(self.inputs, variable), True
        )

    @classmethod
    def from_toml(cls, path: str) -> Model:
        """Load a model from a TOML file.

        Parameters
        ----------

        path: `str`
            TOML file path.
        """
        model = cls.__new__(cls)
        model._m = CModel()
        err = model._m.from_toml(path)
        if err.getInt(0) != 0:
            raise RuntimeError(err.getString(0))
        return model

    def to_toml(
        self,
        path: str,
        tree: Optional[Tree] = None,
    ) -> None:
        """
        Dump the model to a TOML file.

        Parameters
        ----------
        path: `str`
            TOML file path.

        tree: `Tree`, optional
            The `Tree` object to write in the TOML file. If None, write the
            `Tree` object associated with the `tree` model attribute.
        """
        if tree is None:
            tree = self.tree
        err = self._m.to_toml(path, tree._m)
        if err.getInt(0) != 0:
            raise RuntimeError(err.getString(0))

    def _input_to_dataframe(self, data, nan_nodata=False):
        d = data.data
        if np.size(d) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(
            data=d, index=data.dates,
            columns=range(1, d.shape[1] + 1)
        )
        df.index.name = "dates"
        df.columns.name = "zones"
        if nan_nodata:
            df = df.where(df != data.nodata, np.nan)
        return df

    @property
    @wrap_property(InputCollection)
    def inputs(self) -> InputCollection:
        """Model input data.

        Returns
        -------
        `InputCollection`
        """
        return self._m.getInputs()
    
    @inputs.setter
    def inputs(self, v: InputCollection) -> None:
        e = self._m.setInputs(v._m)
        if e.getInt(0) != 0:
            raise RuntimeError(e.getString(0))