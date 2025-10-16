"""
Energy System catalog heat generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.catalog_factories.data_models.energy_systems.generation_system import GenerationSystem


class PvGenerationSystem(GenerationSystem):
  """
  Electricity Generation system class
  """

  def __init__(self, system_id, name, system_type, model_name=None, manufacturer=None, electricity_efficiency=None,
               nominal_electricity_output=None, nominal_ambient_temperature=None, nominal_cell_temperature=None,
               nominal_radiation=None, standard_test_condition_cell_temperature=None,
               standard_test_condition_maximum_power=None, standard_test_condition_radiation=None,
               cell_temperature_coefficient=None, width=None, height=None, distribution_systems=None,
               energy_storage_systems=None):
    super().__init__(system_id=system_id, name=name, model_name=model_name,
                     manufacturer=manufacturer, fuel_type='renewable', distribution_systems=distribution_systems,
                     energy_storage_systems=energy_storage_systems)
    self._system_type = system_type
    self._electricity_efficiency = electricity_efficiency
    self._nominal_electricity_output = nominal_electricity_output
    self._nominal_ambient_temperature = nominal_ambient_temperature
    self._nominal_cell_temperature = nominal_cell_temperature
    self._nominal_radiation = nominal_radiation
    self._standard_test_condition_cell_temperature = standard_test_condition_cell_temperature
    self._standard_test_condition_maximum_power = standard_test_condition_maximum_power
    self._standard_test_condition_radiation = standard_test_condition_radiation
    self._cell_temperature_coefficient = cell_temperature_coefficient
    self._width = width
    self._height = height

  @property
  def system_type(self):
    """
    Get type
    :return: string
    """
    return self._system_type

  @property
  def nominal_electricity_output(self):
    """
    Get nominal_power_output of electricity generation devices or inverters in W
    :return: float
    """
    return self._nominal_electricity_output

  @property
  def electricity_efficiency(self):
    """
    Get electricity_efficiency
    :return: float
    """
    return self._electricity_efficiency

  @property
  def nominal_ambient_temperature(self):
    """
    Get nominal ambient temperature of PV panels in degree Celsius
    :return: float
    """
    return self._nominal_ambient_temperature

  @property
  def nominal_cell_temperature(self):
    """
    Get nominal cell temperature of PV panels in degree Celsius
    :return: float
    """
    return self._nominal_cell_temperature

  @property
  def nominal_radiation(self):
    """
    Get nominal radiation of PV panels
    :return: float
    """
    return self._nominal_radiation

  @property
  def standard_test_condition_cell_temperature(self):
    """
    Get standard test condition cell temperature of PV panels in degree Celsius
    :return: float
    """
    return self._standard_test_condition_cell_temperature

  @property
  def standard_test_condition_maximum_power(self):
    """
    Get standard test condition maximum power of PV panels in W
    :return: float
    """
    return self._standard_test_condition_maximum_power

  @property
  def standard_test_condition_radiation(self):
    """
    Get standard test condition cell temperature of PV panels in W/m2
    :return: float
    """
    return self._standard_test_condition_radiation


  @property
  def cell_temperature_coefficient(self):
    """
    Get cell temperature coefficient of PV module
    :return: float
    """
    return self._cell_temperature_coefficient

  @property
  def width(self):
    """
    Get PV module width in m
    :return: float
    """
    return self._width

  @property
  def height(self):
    """
    Get PV module height in m
    :return: float
    """
    return self._height

  def to_dictionary(self):
    """Class content to dictionary"""
    _distribution_systems = [_distribution_system.to_dictionary() for _distribution_system in
                             self.distribution_systems] if self.distribution_systems is not None else None
    _energy_storage_systems = [_energy_storage_system.to_dictionary() for _energy_storage_system in
                               self.energy_storage_systems] if self.energy_storage_systems is not None else None
    content = {
      'Energy Generation component':
      {
        'id': self.id,
        'model name': self.model_name,
        'manufacturer': self.manufacturer,
        'type': self.system_type,
        'fuel type': self.fuel_type,
        'electricity efficiency': self.electricity_efficiency,
        'nominal power output [W]': self.nominal_electricity_output,
        'nominal ambient temperature [Celsius]': self.nominal_ambient_temperature,
        'nominal cell temperature [Celsius]': self.nominal_cell_temperature,
        'nominal radiation [W/m2]': self.nominal_radiation,
        'standard test condition cell temperature [Celsius]': self.standard_test_condition_cell_temperature,
        'standard test condition maximum power [W]': self.standard_test_condition_maximum_power,
        'standard test condition radiation [W/m2]': self.standard_test_condition_radiation,
        'cell temperature coefficient': self.cell_temperature_coefficient,
        'width': self.width,
        'height': self.height,
        'distribution systems connected': _distribution_systems,
        'storage systems connected': _energy_storage_systems
      }
    }
    return content
