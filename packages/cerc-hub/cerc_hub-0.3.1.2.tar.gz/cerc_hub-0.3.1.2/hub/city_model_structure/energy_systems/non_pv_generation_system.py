"""
Non PV energy generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from typing import Union

from hub.city_model_structure.energy_systems.generation_system import GenerationSystem
from hub.city_model_structure.energy_systems.performance_curve import PerformanceCurves


class NonPvGenerationSystem(GenerationSystem):
  """
  NonPvGenerationSystem class
  """
  def __init__(self):
    super().__init__()
    self._nominal_heat_output = None
    self._maximum_heat_output = None
    self._minimum_heat_output = None
    self._heat_efficiency = None
    self._nominal_cooling_output = None
    self._maximum_cooling_output = None
    self._minimum_cooling_output = None
    self._cooling_efficiency = None
    self._electricity_efficiency = None
    self._nominal_electricity_output = None
    self._source_medium = None
    self._source_temperature = None
    self._source_mass_flow = None
    self._supply_medium = None
    self._maximum_heat_supply_temperature = None
    self._minimum_heat_supply_temperature = None
    self._maximum_cooling_supply_temperature = None
    self._minimum_cooling_supply_temperature = None
    self._heat_output_curve = None
    self._heat_fuel_consumption_curve = None
    self._heat_efficiency_curve = None
    self._cooling_output_curve = None
    self._cooling_fuel_consumption_curve = None
    self._cooling_efficiency_curve = None
    self._domestic_hot_water = None
    self._heat_supply_temperature = None
    self._cooling_supply_temperature = None
    self._reversible = None
    self._simultaneous_heat_cold = None
    self._energy_consumption = {}

  @property
  def nominal_heat_output(self):
    """
    Get nominal heat output of heat generation devices in W
    :return: float
    """
    return self._nominal_heat_output

  @nominal_heat_output.setter
  def nominal_heat_output(self, value):
    """
    Set nominal heat output of heat generation devices in W
    :param value: float
    """
    self._nominal_heat_output = value

  @property
  def maximum_heat_output(self):
    """
    Get maximum heat output of heat generation devices in W
    :return: float
    """
    return self._maximum_heat_output

  @maximum_heat_output.setter
  def maximum_heat_output(self, value):
    """
    Set maximum heat output of heat generation devices in W
    :param value: float
    """
    self._maximum_heat_output = value

  @property
  def minimum_heat_output(self):
    """
    Get minimum heat output of heat generation devices in W
    :return: float
    """
    return self._minimum_heat_output

  @minimum_heat_output.setter
  def minimum_heat_output(self, value):
    """
    Set minimum heat output of heat generation devices in W
    :param value: float
    """
    self._minimum_heat_output = value

  @property
  def source_medium(self):
    """
    Get source_type from [air, water, ground, district_heating, grid, on_site_electricity]
    :return: string
    """
    return self._source_medium

  @source_medium.setter
  def source_medium(self, value):
    """
    Set source medium from [Air, Water, Geothermal, District Heating, Grid, Onsite Electricity]
    :param value: [string]
    """
    self._source_medium = value

  @property
  def supply_medium(self):
    """
    Get the supply medium from ['air', 'water']
    :return: string
    """
    return self._supply_medium

  @supply_medium.setter
  def supply_medium(self, value):
    """
    Set the supply medium from ['air', 'water']
    :param value: string
    """
    self._supply_medium = value

  @property
  def heat_efficiency(self):
    """
    Get heat_efficiency
    :return: float
    """
    return self._heat_efficiency

  @heat_efficiency.setter
  def heat_efficiency(self, value):
    """
    Set heat_efficiency
    :param value: float
    """
    self._heat_efficiency = value

  @property
  def nominal_cooling_output(self):
    """
    Get nominal cooling output of heat generation devices in W
    :return: float
    """
    return self._nominal_cooling_output

  @nominal_cooling_output.setter
  def nominal_cooling_output(self, value):
    """
    Set nominal cooling output of heat generation devices in W
    :param value: float
    """
    self._nominal_cooling_output = value

  @property
  def maximum_cooling_output(self):
    """
    Get maximum heat output of heat generation devices in W
    :return: float
    """
    return self._maximum_cooling_output

  @maximum_cooling_output.setter
  def maximum_cooling_output(self, value):
    """
    Set maximum heat output of heat generation devices in W
    :param value: float
    """
    self._maximum_cooling_output = value

  @property
  def minimum_cooling_output(self):
    """
    Get minimum heat output of heat generation devices in W
    :return: float
    """
    return self._minimum_cooling_output

  @minimum_cooling_output.setter
  def minimum_cooling_output(self, value):
    """
    Set minimum heat output of heat generation devices in W
    :param value: float
    """
    self._minimum_cooling_output = value

  @property
  def cooling_efficiency(self):
    """
    Get cooling_efficiency
    :return: float
    """
    return self._cooling_efficiency

  @cooling_efficiency.setter
  def cooling_efficiency(self, value):
    """
    Set cooling_efficiency
    :param value: float
    """
    self._cooling_efficiency = value

  @property
  def electricity_efficiency(self):
    """
    Get electricity_efficiency
    :return: float
    """
    return self._electricity_efficiency

  @electricity_efficiency.setter
  def electricity_efficiency(self, value):
    """
    Set electricity_efficiency
    :param value: float
    """
    self._electricity_efficiency = value

  @property
  def source_temperature(self):
    """
    Get source_temperature in degree Celsius
    :return: float
    """
    return self._source_temperature

  @source_temperature.setter
  def source_temperature(self, value):
    """
    Set source_temperature in degree Celsius
    :param value: float
    """
    self._source_temperature = value

  @property
  def source_mass_flow(self):
    """
    Get source_mass_flow in kg/s
    :return: float
    """
    return self._source_mass_flow

  @source_mass_flow.setter
  def source_mass_flow(self, value):
    """
    Set source_mass_flow in kg/s
    :param value: float
    """
    self._source_mass_flow = value

  @property
  def nominal_electricity_output(self):
    """
    Get nominal_power_output of electricity generation devices or inverters in W
    :return: float
    """
    return self._nominal_electricity_output

  @nominal_electricity_output.setter
  def nominal_electricity_output(self, value):
    """
    Get nominal_power_output of electricity generation devices or inverters in W
    :param value: float
    """
    self._nominal_electricity_output = value

  @property
  def maximum_heat_supply_temperature(self):
    """
    Get the maximum heat supply temperature in degree Celsius
    :return: float
    """
    return self._minimum_heat_supply_temperature

  @maximum_heat_supply_temperature.setter
  def maximum_heat_supply_temperature(self, value):
    """
    Set maximum heating supply temperature in degree Celsius
    :param value: float
    """
    self._maximum_heat_supply_temperature = value

  @property
  def minimum_heat_supply_temperature(self):
    """
    Get the minimum heat supply temperature in degree Celsius
    :return: float
    """
    return self._minimum_heat_supply_temperature

  @minimum_heat_supply_temperature.setter
  def minimum_heat_supply_temperature(self, value):
    """
    Set minimum heating supply temperature in degree Celsius
    :param value: float
    """
    self._minimum_heat_supply_temperature = value

  @property
  def maximum_cooling_supply_temperature(self):
    """
    Get the maximum cooling supply temperature in degree Celsius
    :return: float
    """
    return self._maximum_cooling_supply_temperature

  @maximum_cooling_supply_temperature.setter
  def maximum_cooling_supply_temperature(self, value):
    """
    Set maximum cooling supply temperature in degree Celsius
    :param value: float
    """
    self._maximum_cooling_supply_temperature = value

  @property
  def minimum_cooling_supply_temperature(self):
    """
    Get the minimum cooling supply temperature in degree Celsius
    :return: float
    """
    return self._minimum_cooling_supply_temperature

  @minimum_cooling_supply_temperature.setter
  def minimum_cooling_supply_temperature(self, value):
    """
    Set minimum cooling supply temperature in degree Celsius
    :param value: float
    """
    self._minimum_cooling_supply_temperature = value

  @property
  def heat_output_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heat output curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._heat_output_curve

  @heat_output_curve.setter
  def heat_output_curve(self, value):
    """
    Set the heat output curve of the heat generation device
    :return: PerformanceCurve
    """
    self._heat_output_curve = value

  @property
  def heat_fuel_consumption_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating fuel consumption curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._heat_fuel_consumption_curve

  @heat_fuel_consumption_curve.setter
  def heat_fuel_consumption_curve(self, value):
    """
    Set the heating fuel consumption curve of the heat generation device
    :return: PerformanceCurve
    """
    self._heat_fuel_consumption_curve = value

  @property
  def heat_efficiency_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating efficiency curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._heat_efficiency_curve

  @heat_efficiency_curve.setter
  def heat_efficiency_curve(self, value):
    """
    Set the heating efficiency curve of the heat generation device
    :return: PerformanceCurve
    """
    self._heat_efficiency_curve = value

  @property
  def cooling_output_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heat output curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._cooling_output_curve

  @cooling_output_curve.setter
  def cooling_output_curve(self, value):
    """
    Set the cooling output curve of the heat generation device
    :return: PerformanceCurve
    """
    self._cooling_output_curve = value

  @property
  def cooling_fuel_consumption_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating fuel consumption curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._cooling_fuel_consumption_curve

  @cooling_fuel_consumption_curve.setter
  def cooling_fuel_consumption_curve(self, value):
    """
    Set the heating fuel consumption curve of the heat generation device
    :return: PerformanceCurve
    """
    self._cooling_fuel_consumption_curve = value

  @property
  def cooling_efficiency_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating efficiency curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._cooling_efficiency_curve

  @cooling_efficiency_curve.setter
  def cooling_efficiency_curve(self, value):
    """
    Set the heating efficiency curve of the heat generation device
    :return: PerformanceCurve
    """
    self._cooling_efficiency_curve = value

  @property
  def domestic_hot_water(self):
    """
    Get the capability of generating domestic hot water

    :return: bool
    """
    return self._domestic_hot_water

  @domestic_hot_water.setter
  def domestic_hot_water(self, value):
    """
    Set the capability of generating domestic hot water

    :return: bool
    """
    self._domestic_hot_water = value

  @property
  def heat_supply_temperature(self):
    """
    Get the hourly heat supply temperature
    :return: list
    """
    return self._heat_supply_temperature

  @heat_supply_temperature.setter
  def heat_supply_temperature(self, value):
    """
    set the hourly heat supply temperature
    :param value:
    :return: list
    """
    self._heat_supply_temperature = value

  @property
  def cooling_supply_temperature(self):
    """
    Get the hourly cooling supply temperature
    :return: list
    """
    return self._heat_supply_temperature

  @cooling_supply_temperature.setter
  def cooling_supply_temperature(self, value):
    """
    set the hourly cooling supply temperature
    :param value:
    :return: list
    """
    self._cooling_supply_temperature = value

  @property
  def reversibility(self):
    """
    Get the capability of generating both heating and cooling

    :return: bool
    """
    return self._reversible

  @reversibility.setter
  def reversibility(self, value):
    """
    Set the capability of generating domestic hot water

    :return: bool
    """
    self._reversible = value

  @property
  def simultaneous_heat_cold(self):
    """
    Get the capability of generating both heating and cooling at the same time

    :return: bool
    """
    return self._simultaneous_heat_cold

  @simultaneous_heat_cold.setter
  def simultaneous_heat_cold(self, value):
    """
    Set the capability of generating domestic hot water at the same time

    :return: bool
    """
    self._simultaneous_heat_cold = value

  @property
  def energy_consumption(self) -> dict:
    """
    Get energy consumption in W
    :return: dict{[float]}
    """
    return self._energy_consumption

  @energy_consumption.setter
  def energy_consumption(self, value):
    """
    Set energy consumption in W
    :param value: dict{[float]}
    """
    self._energy_consumption = value

