"""
PV energy generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from hub.city_model_structure.energy_systems.generation_system import GenerationSystem


class PvGenerationSystem(GenerationSystem):
  """
  PvGenerationSystem class
  """
  def __init__(self):
    super().__init__()
    self._electricity_efficiency = None
    self._nominal_electricity_output = None
    self._nominal_ambient_temperature = None
    self._nominal_cell_temperature = None
    self._nominal_radiation = None
    self._standard_test_condition_cell_temperature = None
    self._standard_test_condition_maximum_power = None
    self._standard_test_condition_radiation = None
    self._cell_temperature_coefficient = None
    self._width = None
    self._height = None
    self._electricity_power_output = {}
    self._tilt_angle = None
    self._installed_capacity = None

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
    Set nominal_power_output of electricity generation devices or inverters in W
    :param value: float
    """
    self._nominal_electricity_output = value

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
  def nominal_ambient_temperature(self):
    """
    Get nominal ambient temperature of PV panels in degree Celsius
    :return: float
    """
    return self._nominal_ambient_temperature

  @nominal_ambient_temperature.setter
  def nominal_ambient_temperature(self, value):
    """
    Set nominal ambient temperature of PV panels in degree Celsius
    :param value: float
    """
    self._nominal_ambient_temperature = value

  @property
  def nominal_cell_temperature(self):
    """
    Get nominal cell temperature of PV panels in degree Celsius
    :return: float
    """
    return self._nominal_cell_temperature

  @nominal_cell_temperature.setter
  def nominal_cell_temperature(self, value):
    """
    Set nominal cell temperature of PV panels in degree Celsius
    :param value: float
    """
    self._nominal_cell_temperature = value

  @property
  def nominal_radiation(self):
    """
    Get nominal radiation of PV panels
    :return: float
    """
    return self._nominal_radiation

  @nominal_radiation.setter
  def nominal_radiation(self, value):
    """
    Set nominal radiation of PV panels
    :param value: float
    """
    self._nominal_radiation = value

  @property
  def standard_test_condition_cell_temperature(self):
    """
    Get standard test condition cell temperature of PV panels in degree Celsius
    :return: float
    """
    return self._standard_test_condition_cell_temperature

  @standard_test_condition_cell_temperature.setter
  def standard_test_condition_cell_temperature(self, value):
    """
    Set standard test condition cell temperature of PV panels in degree Celsius
    :param value: float
    """
    self._standard_test_condition_cell_temperature = value

  @property
  def standard_test_condition_maximum_power(self):
    """
    Get standard test condition maximum power of PV panels in W
    :return: float
    """
    return self._standard_test_condition_maximum_power

  @standard_test_condition_maximum_power.setter
  def standard_test_condition_maximum_power(self, value):
    """
    Set standard test condition maximum power of PV panels in W
    :param value: float
    """
    self._standard_test_condition_maximum_power = value

  @property
  def standard_test_condition_radiation(self):
    """
    Get standard test condition radiation in W/m2
    :return: float
    """
    return self._standard_test_condition_radiation

  @standard_test_condition_radiation.setter
  def standard_test_condition_radiation(self, value):
    """
    Set standard test condition radiation in W/m2
    :param value: float
    """
    self._standard_test_condition_radiation = value

  @property
  def cell_temperature_coefficient(self):
    """
    Get cell temperature coefficient of PV module
    :return: float
    """
    return self._cell_temperature_coefficient

  @cell_temperature_coefficient.setter
  def cell_temperature_coefficient(self, value):
    """
    Set cell temperature coefficient of PV module
    :param value: float
    """
    self._cell_temperature_coefficient = value

  @property
  def width(self):
    """
    Get PV module width in m
    :return: float
    """
    return self._width

  @width.setter
  def width(self, value):
    """
    Set PV module width in m
    :param value: float
    """
    self._width = value

  @property
  def height(self):
    """
    Get PV module height in m
    :return: float
    """
    return self._height

  @height.setter
  def height(self, value):
    """
    Set PV module height in m
    :param value: float
    """
    self._height = value

  @property
  def electricity_power_output(self):
    """
    Get electricity_power in W
    :return: float
    """
    return self._electricity_power_output

  @electricity_power_output.setter
  def electricity_power_output(self, value):
    """
    Set electricity_power in W
    :param value: float
    """
    self._electricity_power_output = value

  @property
  def installed_capacity(self):
    """
    Get the total installed nominal capacity in W
    :return: float
    """
    return self._installed_capacity

  @installed_capacity.setter
  def installed_capacity(self, value):
    """
    Set the total installed nominal capacity in W
    :param value: float
    """
    self._installed_capacity = value
