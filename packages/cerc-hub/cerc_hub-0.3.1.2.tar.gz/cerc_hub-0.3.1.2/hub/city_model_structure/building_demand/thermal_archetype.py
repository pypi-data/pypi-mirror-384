"""
Thermal archetype module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.city_model_structure.building_demand.construction import Construction


class ThermalArchetype:
  """
  ThermalArchetype class
  """
  def __init__(self):
    self._constructions = None
    self._average_storey_height = None
    self._thermal_capacity = None
    self._extra_loses_due_to_thermal_bridges = None
    self._indirect_heated_ratio = None
    self._infiltration_rate_for_ventilation_system_off = None
    self._infiltration_rate_for_ventilation_system_on = None
    self._infiltration_rate_area_for_ventilation_system_off=None
    self._infiltration_rate_area_for_ventilation_system_on=None

  @property
  def constructions(self) -> [Construction]:
    """
    Get archetype constructions
    :return: [Construction]
    """
    return self._constructions

  @constructions.setter
  def constructions(self, value):
    """
    Set archetype constructions
    :param value: [Construction]
    """
    self._constructions = value

  @property
  def average_storey_height(self):
    """
    Get average storey height in m
    :return: float
    """
    return self._average_storey_height

  @average_storey_height.setter
  def average_storey_height(self, value):
    """
    Set average storey height in m
    :param value: float
    """
    self._average_storey_height = value

  @property
  def thermal_capacity(self):
    """
    Get thermal capacity in J/m3K
    :return: float
    """
    return self._thermal_capacity

  @thermal_capacity.setter
  def thermal_capacity(self, value):
    """
    Set thermal capacity in J/m3K
    :param value: float
    """
    self._thermal_capacity = value

  @property
  def extra_loses_due_to_thermal_bridges(self):
    """
    Get extra loses due to thermal bridges in W/m2K
    :return: float
    """
    return self._extra_loses_due_to_thermal_bridges

  @extra_loses_due_to_thermal_bridges.setter
  def extra_loses_due_to_thermal_bridges(self, value):
    """
    Set extra loses due to thermal bridges in W/m2K
    :param value: float
    """
    self._extra_loses_due_to_thermal_bridges = value

  @property
  def indirect_heated_ratio(self):
    """
    Get indirect heated area ratio
    :return: float
    """
    return self._indirect_heated_ratio

  @indirect_heated_ratio.setter
  def indirect_heated_ratio(self, value):
    """
    Set indirect heated area ratio
    :param value: float
    """
    self._indirect_heated_ratio = value

  @property
  def infiltration_rate_for_ventilation_system_off(self):
    """
    Get infiltration rate for ventilation system off in ACH
    :return: float
    """
    return self._infiltration_rate_for_ventilation_system_off

  @infiltration_rate_for_ventilation_system_off.setter
  def infiltration_rate_for_ventilation_system_off(self, value):
    """
    Set infiltration rate for ventilation system off in ACH
    :param value: float
    """
    self._infiltration_rate_for_ventilation_system_off = value

  @property
  def infiltration_rate_for_ventilation_system_on(self):
    """
    Get infiltration rate for ventilation system on in ACH
    :return: float
    """
    return self._infiltration_rate_for_ventilation_system_on

  @infiltration_rate_for_ventilation_system_on.setter
  def infiltration_rate_for_ventilation_system_on(self, value):
    """
    Set infiltration rate for ventilation system on in ACH
    :param value: float
    """
    self._infiltration_rate_for_ventilation_system_on = value

  @property
  def infiltration_rate_area_for_ventilation_system_off(self):
    """
    Get infiltration rate for ventilation system off in m3/s/m2
    :return: float
    """
    return self._infiltration_rate_area_for_ventilation_system_off

  @infiltration_rate_area_for_ventilation_system_off.setter
  def infiltration_rate_area_for_ventilation_system_off(self, value):
    """
    Set infiltration rate for ventilation system off in m3/s/m2
    :param value: float
    """
    self._infiltration_rate_area_for_ventilation_system_off = value

  @property
  def infiltration_rate_area_for_ventilation_system_on(self):
    """
    Get infiltration rate for ventilation system on in m3/s/m2
    :return: float
    """
    return self._infiltration_rate_area_for_ventilation_system_on

  @infiltration_rate_area_for_ventilation_system_on.setter
  def infiltration_rate_area_for_ventilation_system_on(self, value):
    """
    Set infiltration rate for ventilation system on in m3/s/m2
    :param value: float
    """
    self._infiltration_rate_area_for_ventilation_system_on = value
