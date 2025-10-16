"""
Construction catalog Archetype
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.catalog_factories.data_models.construction.construction import Construction


class Archetype:
  """
  Archetype class
  """
  def __init__(self, archetype_id,
               name,
               function,
               climate_zone,
               construction_period,
               constructions,
               average_storey_height,
               thermal_capacity,
               extra_loses_due_to_thermal_bridges,
               indirect_heated_ratio,
               infiltration_rate_for_ventilation_system_off,
               infiltration_rate_for_ventilation_system_on,
               infiltration_rate_area_for_ventilation_system_off,
               infiltration_rate_area_for_ventilation_system_on
               ):
    self._id = archetype_id
    self._name = name
    self._function = function
    self._climate_zone = climate_zone
    self._construction_period = construction_period
    self._constructions = constructions
    self._average_storey_height = average_storey_height
    self._thermal_capacity = thermal_capacity
    self._extra_loses_due_to_thermal_bridges = extra_loses_due_to_thermal_bridges
    self._indirect_heated_ratio = indirect_heated_ratio
    self._infiltration_rate_for_ventilation_system_off = infiltration_rate_for_ventilation_system_off
    self._infiltration_rate_for_ventilation_system_on = infiltration_rate_for_ventilation_system_on
    self._infiltration_rate_area_for_ventilation_system_off = infiltration_rate_area_for_ventilation_system_off
    self._infiltration_rate_area_for_ventilation_system_on = infiltration_rate_area_for_ventilation_system_on

  @property
  def id(self):
    """
    Get archetype id
    :return: str
    """
    return self._id

  @property
  def name(self):
    """
    Get archetype name
    :return: str
    """
    return self._name

  @property
  def function(self):
    """
    Get archetype function
    :return: str
    """
    return self._function

  @property
  def climate_zone(self):
    """
    Get archetype climate zone
    :return: str
    """
    return self._climate_zone

  @property
  def constructions(self) -> [Construction]:
    """
    Get archetype constructions
    :return: [Construction]
    """
    return self._constructions

  @property
  def construction_period(self):
    """
    Get archetype construction period
    :return: str
    """
    return self._construction_period

  @property
  def average_storey_height(self):
    """
    Get archetype average storey height in m
    :return: float
    """
    return self._average_storey_height

  @property
  def thermal_capacity(self):
    """
    Get archetype thermal capacity in J/m3K
    :return: float
    """
    return self._thermal_capacity

  @property
  def extra_loses_due_to_thermal_bridges(self):
    """
    Get archetype extra loses due to thermal bridges in W/m2K
    :return: float
    """
    return self._extra_loses_due_to_thermal_bridges

  @property
  def indirect_heated_ratio(self):
    """
    Get archetype indirect heated area ratio
    :return: float
    """
    return self._indirect_heated_ratio

  @property
  def infiltration_rate_for_ventilation_system_off(self):
    """
    Get archetype infiltration rate for ventilation system off in 1/s
    :return: float
    """
    return self._infiltration_rate_for_ventilation_system_off

  @property
  def infiltration_rate_for_ventilation_system_on(self):
    """
    Get archetype infiltration rate for ventilation system on in 1/s
    :return: float
    """
    return self._infiltration_rate_for_ventilation_system_on

  @property
  def infiltration_rate_area_for_ventilation_system_off(self):
    """
    Get archetype infiltration rate for ventilation system off in m3/sm2
    :return: float
    """
    return self._infiltration_rate_area_for_ventilation_system_off

  @property
  def infiltration_rate_area_for_ventilation_system_on(self):
    """
    Get archetype infiltration rate for ventilation system on in m3/sm2
    :return: float
    """
    return self._infiltration_rate_for_ventilation_system_on

  def to_dictionary(self):
    """Class content to dictionary"""
    _constructions = []
    for _construction in self.constructions:
      _constructions.append(_construction.to_dictionary())
    content = {'Archetype': {'id': self.id,
                             'name': self.name,
                             'function': self.function,
                             'climate zone': self.climate_zone,
                             'period of construction': self.construction_period,
                             'average storey height [m]': self.average_storey_height,
                             'thermal capacity [J/m3K]': self.thermal_capacity,
                             'extra loses due to thermal bridges [W/m2K]': self.extra_loses_due_to_thermal_bridges,
                             'indirect heated ratio': self.indirect_heated_ratio,
                             'infiltration rate for ventilation off [1/s]': self.infiltration_rate_for_ventilation_system_off,
                             'infiltration rate for ventilation on [1/s]': self.infiltration_rate_for_ventilation_system_on,
                             'infiltration rate area for ventilation off [m3/sm2]': self.infiltration_rate_area_for_ventilation_system_off,
                             'infiltration rate area for ventilation on [m3/sm2]': self.infiltration_rate_area_for_ventilation_system_on,
                             'constructions': _constructions
                             }
               }
    return content
