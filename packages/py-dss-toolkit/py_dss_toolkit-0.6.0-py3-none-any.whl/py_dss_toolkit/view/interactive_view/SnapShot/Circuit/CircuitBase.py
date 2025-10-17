# -*- coding: utf-8 -*-
# @Author  : Paulo Radatz
# @Email   : paulo.radatz@gmail.com
# @File    : CircuitBase.py
# @Software: PyCharm

import numpy as np
import pandas as pd
from typing import Optional, List
from py_dss_interface import DSS
from py_dss_toolkit.results.SnapShot.SnapShotPowerFlowResults import SnapShotPowerFlowResults
from py_dss_toolkit.model.ModelBase import ModelBase
from py_dss_toolkit.view.interactive_view.InteractiveCustomPlotStyle import InteractiveCustomPlotStyle
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.ActivePowerSettings import ActivePowerSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.VoltageSettings import VoltageSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.UserDefinedNumericalSettings import UserDefinedNumericalSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.UserDefinedCategoricalSettings import UserDefinedCategoricalSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.PhasesSettings import PhasesSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.ThermalViolationSettings import ThermalViolationSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.VoltageViolationSettings import VoltageViolationSettings
from py_dss_toolkit.view.interactive_view.SnapShot.Circuit.CircuitBusMarker import CircuitBusMarker


class PlotParameterStrategy:
    """Base class for plot parameter strategies."""
    
    def __init__(self, circuit_instance):
        self._circuit = circuit_instance
    
    def get_settings_and_results(self):
        """Return (settings, results, hovertemplate, numerical_plot)"""
        raise NotImplementedError


class ActivePowerStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._active_power_settings
        columns = self._circuit._results.powers_elements[0].columns
        if "Terminal1.1" not in columns or "Terminal1.2" not in columns or "Terminal1.3" not in columns:
            raise ValueError("A non 3-phase circuit can't be plotted")
        results = self._circuit._results.powers_elements[0].loc[:, ["Terminal1.1", "Terminal1.2", "Terminal1.3"]].sum(axis=1)
        hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                        "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>" +
                        "<b>Total P: </b>%{customdata[3]:.2f} kW<br>")
        return settings, results, hovertemplate, True


class ReactivePowerStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._active_power_settings
        columns = self._circuit._results.powers_elements[1].columns
        if "Terminal1.1" not in columns or "Terminal1.2" not in columns or "Terminal1.3" not in columns:
            raise ValueError("A non 3-phase circuit can't be plotted")
        results = self._circuit._results.powers_elements[0].loc[:, ["Terminal1.1", "Terminal1.2", "Terminal1.3"]].sum(axis=1)
        hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                        "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>" +
                        "<b>Total Q: </b>%{customdata[3]:.2f} kvar<br>")
        return settings, results, hovertemplate, True


class VoltageStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._voltage_settings
        bus = settings.bus
        columns = self._circuit._results.voltages_elements[0].columns
        if bus == "bus1":
            p = 1
        else:
            p = 2
        if "Terminal1.1" not in columns or "Terminal1.2" not in columns or "Terminal1.3" not in columns:
            raise ValueError("A non 3-phase circuit can't be plotted")
        v = self._circuit._results.voltages_elements[0].loc[:, [f"Terminal{p}.1", f"Terminal{p}.2", f"Terminal{p}.3"]]
        if settings.nodes_voltage_value == "mean":
            results = v.mean(axis=1)
        elif settings.nodes_voltage_value == "min":
            results = v.min(axis=1)
        elif settings.nodes_voltage_value == "max":
            results = v.max(axis=1)
        hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                        "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>" +
                        f"<b>{settings.nodes_voltage_value.capitalize()} {bus.capitalize()} Voltage: </b>" +
                        "%{customdata[3]:.4f} pu<br>")
        return settings, results, hovertemplate, True


class UserNumericalDefinedStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._user_numerical_defined_settings
        parameter = settings.parameter
        unit = settings.unit
        num_decimal_points = settings.num_decimal_points
        if settings.results is None:
            raise ValueError(f"No results found for 'user numerical defined' parameter. "
                           f"Please set the results using: "
                           f"circuit.user_numerical_defined_settings.results = your_data")
        else:
            results = settings.results
            hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                            "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>" +
                            f"<b>{parameter}:</b>" + " %{customdata[3]:" + f".{num_decimal_points}" + "f}" + f" {unit}<br>")
        return settings, results, hovertemplate, True


class PhasesStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._phases_settings
        line_df = self._circuit._model.lines_df
        line_df['name'] = 'line.' + line_df['name']
        results = line_df.set_index("name")["phases"]
        hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                        "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>" +
                        "<b>Phases: </b>%{customdata[3]}<br>")
        return settings, results, hovertemplate, False


class VoltageViolationsStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._voltage_violation_settings
        under_v_bus_violations = self._circuit._results.violation_voltage_ln_nodes[0].index
        over_v_bus_violations = self._circuit._results.violation_voltage_ln_nodes[1].index
        both_v_bus_violations = under_v_bus_violations.intersection(over_v_bus_violations)
        line_df = self._circuit._model.lines_df
        line_df['name'] = 'line.' + line_df['name']
        results = line_df.set_index("name")
        results["bus"] = results['bus1'].str.split('.', n=1).str[0]
        results["violation"] = "0"
        results.loc[results['bus'].isin(under_v_bus_violations), 'violation'] = "1"
        results.loc[results['bus'].isin(over_v_bus_violations), 'violation'] = "2"
        results.loc[results['bus'].isin(both_v_bus_violations), 'violation'] = "3"
        results = results["violation"]
        hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                        "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>")
        return settings, results, hovertemplate, False


class ThermalViolationsStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._thermal_violation_settings
        line_violations = self._circuit._results.violation_currents_elements.index
        line_df = self._circuit._model.lines_df
        line_df['name'] = 'line.' + line_df['name']
        results = line_df.set_index("name")
        results["violation"] = "0"
        results.loc[results.index.isin(line_violations), 'violation'] = "1"
        results = results["violation"]
        hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                        "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>")
        return settings, results, hovertemplate, False


class UserCategoricalDefinedStrategy(PlotParameterStrategy):
    def get_settings_and_results(self):
        settings = self._circuit._user_categorical_defined_settings
        parameter = settings.parameter
        if settings.results is None:
            raise ValueError(f"No results found for 'user categorical defined' parameter. "
                           f"Please set the results using: "
                           f"circuit.user_categorical_defined_settings.results = your_data")
        else:
            results = settings.results
            hovertemplate = ("<b>%{customdata[0]}</b><br>" +
                            "<b>Bus1: </b>%{customdata[1]} | <b>Bus2: </b>%{customdata[2]}<br>" +
                            f"<b>{parameter}:</b>" + " %{customdata[3]}")
        return settings, results, hovertemplate, False


class CircuitBase:
    """Base class containing shared logic for circuit plotting."""

    def __init__(self, dss: DSS, results: SnapShotPowerFlowResults, model: ModelBase):
        self._dss = dss
        self._results = results
        self._model = model
        self._plot_style = InteractiveCustomPlotStyle()
        self._active_power_settings = ActivePowerSettings()
        self._voltage_settings = VoltageSettings()
        self._user_numerical_defined_settings = UserDefinedNumericalSettings()
        self._user_categorical_defined_settings = UserDefinedCategoricalSettings()
        self._phases_settings = PhasesSettings()
        self._thermal_violation_settings = ThermalViolationSettings()
        self._voltage_violation_settings = VoltageViolationSettings()
        
        # Strategy pattern mapping for plot parameters
        self._parameter_strategies = {
            "active power": ActivePowerStrategy(self),
            "reactive power": ReactivePowerStrategy(self),
            "voltage": VoltageStrategy(self),
            "user numerical defined": UserNumericalDefinedStrategy(self),
            "phases": PhasesStrategy(self),
            "voltage violations": VoltageViolationsStrategy(self),
            "thermal violations": ThermalViolationsStrategy(self),
            "user categorical defined": UserCategoricalDefinedStrategy(self)
        }

    def circuit_get_bus_marker(self, name: str, symbol: str = "square",
                               size: float = 10,
                               color: str = "black",
                               marker_name: Optional[str] = None):
        if not marker_name:
            marker_name = name
        return CircuitBusMarker(name=name,
                                symbol=symbol,
                                size=size,
                                color=color,
                                marker_name=marker_name)

    @property
    def circuit_plot_style(self):
        return self._plot_style

    @property
    def active_power_settings(self):
        return self._active_power_settings

    @property
    def voltage_settings(self):
        return self._voltage_settings

    @property
    def user_numerical_defined_settings(self):
        return self._user_numerical_defined_settings

    @property
    def phases_settings(self):
        return self._phases_settings

    @property
    def user_categorical_defined_settings(self):
        return self._user_categorical_defined_settings

    def _get_plot_settings(self, parameter):
        """
        Helper to get settings, results, hovertemplate, and numerical_plot for a given parameter.

        Supported parameters:
            - 'active power': Plots total active power (kW) per line.
            - 'reactive power': Plots total reactive power (kvar) per line.
            - 'voltage': Plots voltage statistics (mean/min/max) per line terminal.
            - 'user numerical defined': Plots user-defined numerical results.
            - 'phases': Plots the number of phases per line.
            - 'user categorical defined': Plots user-defined categorical results.
            - 'voltage violations': Highlights lines connected to buses with voltage violations.
            - 'thermal violations': Highlights lines with thermal (current) violations.

        Returns:
            settings: The settings object for the parameter.
            results: The results Series/DataFrame for plotting.
            hovertemplate: The hovertemplate string for Plotly.
            numerical_plot: Boolean, True if the plot is numerical/continuous, False if categorical/binary.
        """
        if parameter not in self._parameter_strategies:
            raise ValueError(f"Unknown parameter: {parameter}. Supported parameters: {list(self._parameter_strategies.keys())}")
        
        strategy = self._parameter_strategies[parameter]
        return strategy.get_settings_and_results()

    def _prepare_plot_data(self, parameter: str):
        """
        Prepare common data for both circuit_plot and circuit_geoplot methods.
        
        Returns:
            dict: Contains all the data needed for plotting
        """
        settings, results, hovertemplate, numerical_plot = self._get_plot_settings(parameter)
        line_df = self._model.lines_df.copy()
        line_df['name'] = 'line.' + line_df['name']
        num_phases = line_df.set_index("name")["phases"]
        line_type = line_df.set_index("name")["linetype"]

        buses = list()
        bus_coords = list()
        elements_list = [element.lower() for element in self._dss.circuit.elements_names]
        connections = []

        for element in elements_list:
            if element.split(".")[0].lower() in ["line"]:
                self._dss.circuit.set_active_element(element)
                if self._dss.cktelement.is_enabled:
                    bus1, bus2 = self._dss.cktelement.bus_names[0].split(".")[0].lower(), \
                        self._dss.cktelement.bus_names[1].split(".")[0].lower()
                    connections.append([element, (bus1.lower(), bus2.lower())])

                    if bus1 not in buses:
                        self._dss.circuit.set_active_bus(bus1)
                        x, y = self._dss.bus.x, self._dss.bus.y
                        bus_coords.append((x, y))
                        buses.append(bus1)

                    if bus2 not in buses:
                        self._dss.circuit.set_active_bus(bus2)
                        x, y = self._dss.bus.x, self._dss.bus.y
                        bus_coords.append((x, y))
                        buses.append(bus2)
        bus_coords = np.array(bus_coords)

        result_values = list()
        for element in elements_list:
            if element.split(".")[0].lower() in ["line"]:
                self._dss.circuit.set_active_element(element)
                if self._dss.cktelement.is_enabled:
                    result_values.append(results.loc[element])
        result_values = np.array(result_values)

        return {
            'settings': settings,
            'results': results,
            'hovertemplate': hovertemplate,
            'numerical_plot': numerical_plot,
            'line_df': line_df,
            'num_phases': num_phases,
            'line_type': line_type,
            'buses': buses,
            'bus_coords': bus_coords,
            'connections': connections,
            'result_values': result_values
        }

    def _get_phase_width(self, element, num_phases, width_1ph, width_2ph, width_3ph):
        num_phase = int(num_phases[element])
        if num_phase >= 3:
            result = width_3ph
        elif num_phase == 2:
            result = width_2ph
        elif num_phase == 1:
            result = width_1ph
        return result

    def _get_dash(self, element, num_phases, dash_1ph, dash_2ph, dash_3ph, line_type, dash_oh, dash_ug):
        num_phase = int(num_phases[element])
        lt = line_type[element]
        default = 'solid'
        if num_phase >= 3 and dash_3ph is not None:
            return dash_3ph
        elif num_phase == 2 and dash_2ph is not None:
            return dash_2ph
        elif num_phase == 1 and dash_1ph is not None:
            return dash_1ph
        elif lt == 'oh' and dash_oh is not None:
            return dash_oh
        elif lt == 'ug' and dash_ug is not None:
            return dash_ug
        return default
