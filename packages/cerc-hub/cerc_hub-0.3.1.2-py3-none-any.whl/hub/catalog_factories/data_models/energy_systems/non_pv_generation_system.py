"""
Energy System catalog non PV generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from typing import Union
from hub.catalog_factories.data_models.energy_systems.performance_curves import PerformanceCurves
from hub.catalog_factories.data_models.energy_systems.generation_system import GenerationSystem


class NonPvGenerationSystem(GenerationSystem):
  """
  Non PV Generation system class
  """

  def __init__(self, system_id, name, system_type, model_name=None, manufacturer=None, fuel_type=None,
               nominal_heat_output=None, maximum_heat_output=None, minimum_heat_output=None, source_medium=None,
               supply_medium=None, heat_efficiency=None, nominal_cooling_output=None, maximum_cooling_output=None,
               minimum_cooling_output=None, cooling_efficiency=None, electricity_efficiency=None,
               source_temperature=None, source_mass_flow=None, nominal_electricity_output=None,
               maximum_heat_supply_temperature=None, minimum_heat_supply_temperature=None,
               maximum_cooling_supply_temperature=None, minimum_cooling_supply_temperature=None, heat_output_curve=None,
               heat_fuel_consumption_curve=None, heat_efficiency_curve=None, cooling_output_curve=None,
               cooling_fuel_consumption_curve=None, cooling_efficiency_curve=None,
               distribution_systems=None, energy_storage_systems=None, domestic_hot_water=False,
               reversible=None, simultaneous_heat_cold=None):
    super().__init__(system_id=system_id, name=name, model_name=model_name, manufacturer=manufacturer,
                     fuel_type=fuel_type, distribution_systems=distribution_systems,
                     energy_storage_systems=energy_storage_systems)
    self._system_type = system_type
    self._nominal_heat_output = nominal_heat_output
    self._maximum_heat_output = maximum_heat_output
    self._minimum_heat_output = minimum_heat_output
    self._heat_efficiency = heat_efficiency
    self._nominal_cooling_output = nominal_cooling_output
    self._maximum_cooling_output = maximum_cooling_output
    self._minimum_cooling_output = minimum_cooling_output
    self._cooling_efficiency = cooling_efficiency
    self._electricity_efficiency = electricity_efficiency
    self._nominal_electricity_output = nominal_electricity_output
    self._source_medium = source_medium
    self._source_temperature = source_temperature
    self._source_mass_flow = source_mass_flow
    self._supply_medium = supply_medium
    self._maximum_heat_supply_temperature = maximum_heat_supply_temperature
    self._minimum_heat_supply_temperature = minimum_heat_supply_temperature
    self._maximum_cooling_supply_temperature = maximum_cooling_supply_temperature
    self._minimum_cooling_supply_temperature = minimum_cooling_supply_temperature
    self._heat_output_curve = heat_output_curve
    self._heat_fuel_consumption_curve = heat_fuel_consumption_curve
    self._heat_efficiency_curve = heat_efficiency_curve
    self._cooling_output_curve = cooling_output_curve
    self._cooling_fuel_consumption_curve = cooling_fuel_consumption_curve
    self._cooling_efficiency_curve = cooling_efficiency_curve
    self._domestic_hot_water = domestic_hot_water
    self._reversible = reversible
    self._simultaneous_heat_cold = simultaneous_heat_cold

  @property
  def system_type(self):
    """
    Get type
    :return: string
    """
    return self._system_type

  @property
  def nominal_heat_output(self):
    """
    Get nominal heat output of heat generation devices in W
    :return: float
    """
    return self._nominal_heat_output

  @property
  def maximum_heat_output(self):
    """
    Get maximum heat output of heat generation devices in W
    :return: float
    """
    return self._maximum_heat_output

  @property
  def minimum_heat_output(self):
    """
    Get minimum heat output of heat generation devices in W
    :return: float
    """
    return self._minimum_heat_output

  @property
  def source_medium(self):
    """
    Get source_type from [air, water, ground, district_heating, grid, on_site_electricity]
    :return: string
    """
    return self._source_medium

  @property
  def supply_medium(self):
    """
    Get the supply medium from ['air', 'water']
    :return: string
    """
    return self._supply_medium

  @property
  def heat_efficiency(self):
    """
    Get heat_efficiency
    :return: float
    """
    return self._heat_efficiency

  @property
  def nominal_cooling_output(self):
    """
    Get nominal cooling output of heat generation devices in W
    :return: float
    """
    return self._nominal_cooling_output

  @property
  def maximum_cooling_output(self):
    """
    Get maximum heat output of heat generation devices in W
    :return: float
    """
    return self._maximum_cooling_output

  @property
  def minimum_cooling_output(self):
    """
    Get minimum heat output of heat generation devices in W
    :return: float
    """
    return self._minimum_cooling_output

  @property
  def cooling_efficiency(self):
    """
    Get cooling_efficiency
    :return: float
    """
    return self._cooling_efficiency

  @property
  def electricity_efficiency(self):
    """
    Get electricity_efficiency
    :return: float
    """
    return self._electricity_efficiency

  @property
  def source_temperature(self):
    """
    Get source_temperature in degree Celsius
    :return: float
    """
    return self._source_temperature

  @property
  def source_mass_flow(self):
    """
    Get source_mass_flow in kg/s
    :return: float
    """
    return self._source_mass_flow

  @property
  def nominal_electricity_output(self):
    """
    Get nominal_power_output of electricity generation devices or inverters in W
    :return: float
    """
    return self._nominal_electricity_output

  @property
  def maximum_heat_supply_temperature(self):
    """
    Get the maximum heat supply temperature in degree Celsius
    :return: float
    """
    return self._minimum_heat_supply_temperature

  @property
  def minimum_heat_supply_temperature(self):
    """
    Get the minimum heat supply temperature in degree Celsius
    :return: float
    """
    return self._minimum_heat_supply_temperature

  @property
  def maximum_cooling_supply_temperature(self):
    """
    Get the maximum cooling supply temperature in degree Celsius
    :return: float
    """
    return self._maximum_cooling_supply_temperature

  @property
  def minimum_cooling_supply_temperature(self):
    """
    Get the minimum cooling supply temperature in degree Celsius
    :return: float
    """
    return self._minimum_cooling_supply_temperature

  @property
  def heat_output_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heat output curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._heat_output_curve

  @property
  def heat_fuel_consumption_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating fuel consumption curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._heat_fuel_consumption_curve

  @property
  def heat_efficiency_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating efficiency curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._heat_efficiency_curve

  @property
  def cooling_output_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heat output curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._cooling_output_curve

  @property
  def cooling_fuel_consumption_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating fuel consumption curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._cooling_fuel_consumption_curve

  @property
  def cooling_efficiency_curve(self) -> Union[None, PerformanceCurves]:
    """
    Get the heating efficiency curve of the heat generation device
    :return: PerformanceCurve
    """
    return self._cooling_efficiency_curve

  @property
  def domestic_hot_water(self):
    """
    Get the ability to produce domestic hot water
    :return: bool
    """
    return self._domestic_hot_water

  @property
  def reversibility(self):
    """
    Get the ability to produce heating and cooling
    :return: bool
    """
    return self._reversible

  @property
  def simultaneous_heat_cold(self):
    """
    Get the ability to produce heating and cooling at the same time
    :return: bool
    """
    return self._simultaneous_heat_cold

  def to_dictionary(self):
    """Class content to dictionary"""
    _distribution_systems = [_distribution_system.to_dictionary() for _distribution_system in
                             self.distribution_systems] if self.distribution_systems is not None else None
    _energy_storage_systems = [_energy_storage_system.to_dictionary() for _energy_storage_system in
                               self.energy_storage_systems] if self.energy_storage_systems is not None else None
    _heat_output_curve = self.heat_output_curve.to_dictionary() if (
        self.heat_output_curve is not None) else None
    _heat_fuel_consumption_curve = self.heat_fuel_consumption_curve.to_dictionary() if (
        self.heat_fuel_consumption_curve is not None) else None
    _heat_efficiency_curve = self.heat_efficiency_curve.to_dictionary() if (
        self.heat_efficiency_curve is not None) else None
    _cooling_output_curve = self.cooling_output_curve.to_dictionary() if (
        self.cooling_output_curve is not None) else None
    _cooling_fuel_consumption_curve = self.cooling_fuel_consumption_curve.to_dictionary() if (
        self.cooling_fuel_consumption_curve is not None) else None
    _cooling_efficiency_curve = self.cooling_efficiency_curve.to_dictionary() if (
        self.cooling_efficiency_curve is not None) else None

    content = {
      'Energy Generation component':
      {
        'id': self.id,
        'model name': self.model_name,
        'manufacturer': self.manufacturer,
        'type': self.system_type,
        'fuel type': self.fuel_type,
        'nominal heat output [W]': self.nominal_heat_output,
        'maximum heat output [W]': self.maximum_heat_output,
        'minimum heat output [W]': self.minimum_heat_output,
        'source medium': self.source_medium,
        'supply medium': self.supply_medium,
        'source temperature [Celsius]': self.source_temperature,
        'source mass flow [kg/s]': self.source_mass_flow,
        'heat efficiency': self.heat_efficiency,
        'nominal cooling output [W]': self.nominal_cooling_output,
        'maximum cooling output [W]': self.maximum_cooling_output,
        'minimum cooling output [W]': self.minimum_cooling_output,
        'cooling efficiency': self.cooling_efficiency,
        'electricity efficiency': self.electricity_efficiency,
        'nominal power output [W]': self.nominal_electricity_output,
        'maximum heating supply temperature [Celsius]': self.maximum_heat_supply_temperature,
        'minimum heating supply temperature [Celsius]': self.minimum_heat_supply_temperature,
        'maximum cooling supply temperature [Celsius]': self.maximum_cooling_supply_temperature,
        'minimum cooling supply temperature [Celsius]': self.minimum_cooling_supply_temperature,
        'heat output curve': self.heat_output_curve,
        'heat fuel consumption curve': self.heat_fuel_consumption_curve,
        'heat efficiency curve': _heat_efficiency_curve,
        'cooling output curve': self.cooling_output_curve,
        'cooling fuel consumption curve': self.cooling_fuel_consumption_curve,
        'cooling efficiency curve': self.cooling_efficiency_curve,
        'distribution systems connected': _distribution_systems,
        'storage systems connected': _energy_storage_systems,
        'domestic hot water production capability': self.domestic_hot_water,
        'reversible cycle': self.reversibility,
        'simultaneous heat and cooling production': self.simultaneous_heat_cold
      }
    }
    return content
