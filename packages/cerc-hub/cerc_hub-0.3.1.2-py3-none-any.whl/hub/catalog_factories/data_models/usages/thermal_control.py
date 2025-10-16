"""
Usage catalog thermal control
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
from typing import Union, List
from hub.catalog_factories.data_models.usages.schedule import Schedule


class ThermalControl:
  """
  ThermalControl class
  """
  def __init__(self, mean_heating_set_point,
               heating_set_back,
               mean_cooling_set_point,
               hvac_availability_schedules,
               heating_set_point_schedules,
               cooling_set_point_schedules):

    self._mean_heating_set_point = mean_heating_set_point
    self._heating_set_back = heating_set_back
    self._mean_cooling_set_point = mean_cooling_set_point
    self._hvac_availability_schedules = hvac_availability_schedules
    self._heating_set_point_schedules = heating_set_point_schedules
    self._cooling_set_point_schedules = cooling_set_point_schedules

  @property
  def mean_heating_set_point(self) -> Union[None, float]:
    """
    Get heating set point defined for a thermal zone in Celsius
    :return: None or float
    """
    return self._mean_heating_set_point

  @property
  def heating_set_back(self) -> Union[None, float]:
    """
    Get heating set back defined for a thermal zone in Celsius
    :return: None or float
    """
    return self._heating_set_back

  @property
  def mean_cooling_set_point(self) -> Union[None, float]:
    """
    Get cooling set point defined for a thermal zone in Celsius
    :return: None or float
    """
    return self._mean_cooling_set_point

  @property
  def hvac_availability_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get the availability of the conditioning system defined for a thermal zone
    dataType = on/off
    :return: None or [Schedule]
    """
    return self._hvac_availability_schedules

  @property
  def heating_set_point_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get heating set point schedule defined for a thermal zone in Celsius
    dataType = temperature
    :return: None or [Schedule]
    """
    return self._heating_set_point_schedules

  @property
  def cooling_set_point_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get cooling set point schedule defined for a thermal zone in Celsius
    dataType = temperature
    :return: None or [Schedule]
    """
    return self._cooling_set_point_schedules

  def to_dictionary(self):
    """Class content to dictionary"""
    _hvac_schedules = []
    for _schedule in self.hvac_availability_schedules:
      _hvac_schedules.append(_schedule.to_dictionary())
    _heating_set_point_schedules = []
    for _schedule in self.heating_set_point_schedules:
      _heating_set_point_schedules.append(_schedule.to_dictionary())
    _cooling_set_point_schedules = []
    for _schedule in self.cooling_set_point_schedules:
      _cooling_set_point_schedules.append(_schedule.to_dictionary())
    content = {'Thermal control': {'mean heating set point [Celsius]': self.mean_heating_set_point,
                                   'heating set back [Celsius]': self.heating_set_back,
                                   'mean cooling set point [Celsius]': self.mean_cooling_set_point,
                                   'hvac availability schedules': _hvac_schedules,
                                   'heating set point schedules': _heating_set_point_schedules,
                                   'cooling set point schedules': _cooling_set_point_schedules}
               }
    return content
