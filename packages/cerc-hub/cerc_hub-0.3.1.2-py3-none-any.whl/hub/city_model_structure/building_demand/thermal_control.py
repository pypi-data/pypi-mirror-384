"""
ThermalControl module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from math import inf
from typing import Union, List
from hub.city_model_structure.attributes.schedule import Schedule


class ThermalControl:
  """
  ThermalControl class
  """
  def __init__(self):
    self._mean_heating_set_point = None
    self._heating_set_back = None
    self._mean_cooling_set_point = None
    self._hvac_availability_schedules = None
    self._heating_set_point_schedules = None
    self._cooling_set_point_schedules = None

  @staticmethod
  def _maximum_value(schedules):
    maximum = -inf
    for schedule in schedules:
      maximum = max(maximum, max(schedule.values))
    return maximum

  @staticmethod
  def _minimum_value(schedules):
    minimum = inf
    for schedule in schedules:
      minimum = min(minimum, min(schedule.values))
    return minimum

  @property
  def mean_heating_set_point(self) -> Union[None, float]:
    """
    Get heating set point defined for a thermal zone in Celsius
    :return: None or float
    """
    if self._mean_heating_set_point is None:
      if self.heating_set_point_schedules is not None:
        self._mean_heating_set_point = self._maximum_value(self.heating_set_point_schedules)
    return self._mean_heating_set_point

  @mean_heating_set_point.setter
  def mean_heating_set_point(self, value):
    """
    Set heating set point defined for a thermal zone in Celsius
    :param value: float
    """
    self._mean_heating_set_point = float(value)

  @property
  def heating_set_back(self) -> Union[None, float]:
    """
    Get heating set back defined for a thermal zone in Celsius
    :return: None or float
    """
    if self._heating_set_back is None:
      if self.heating_set_point_schedules is not None:
        self._heating_set_back = self._minimum_value(self.heating_set_point_schedules)
    return self._heating_set_back

  @heating_set_back.setter
  def heating_set_back(self, value):
    """
    Set heating set back defined for a thermal zone in Celsius
    :param value: float
    """
    if value is not None:
      self._heating_set_back = float(value)

  @property
  def mean_cooling_set_point(self) -> Union[None, float]:
    """
    Get cooling set point defined for a thermal zone in Celsius
    :return: None or float
    """
    if self._mean_cooling_set_point is None:
      if self.cooling_set_point_schedules is not None:
        self._mean_cooling_set_point = self._minimum_value(self.cooling_set_point_schedules)
    return self._mean_cooling_set_point

  @mean_cooling_set_point.setter
  def mean_cooling_set_point(self, value):
    """
    Set cooling set point defined for a thermal zone in Celsius
    :param value: float
    """
    self._mean_cooling_set_point = float(value)

  @property
  def hvac_availability_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get the availability of the conditioning system defined for a thermal zone
    dataType = on/off
    :return: None or [Schedule]
    """
    return self._hvac_availability_schedules

  @hvac_availability_schedules.setter
  def hvac_availability_schedules(self, value):
    """
    Set the availability of the conditioning system defined for a thermal zone
    dataType = on/off
    :param value: [Schedule]
    """
    self._hvac_availability_schedules = value

  @property
  def heating_set_point_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get heating set point schedule defined for a thermal zone in Celsius
    dataType = temperature
    :return: None or [Schedule]
    """
    return self._heating_set_point_schedules

  @heating_set_point_schedules.setter
  def heating_set_point_schedules(self, value):
    """
    Set heating set point schedule defined for a thermal zone in Celsius
    dataType = temperature
    :param value: [Schedule]
    """
    self._heating_set_point_schedules = value

  @property
  def cooling_set_point_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get cooling set point schedule defined for a thermal zone in Celsius
    dataType = temperature
    :return: None or [Schedule]
    """
    return self._cooling_set_point_schedules

  @cooling_set_point_schedules.setter
  def cooling_set_point_schedules(self, value):
    """
    Set cooling set point schedule defined for a thermal zone in Celsius
    dataType = temperature
    :param value: [Schedule]
    """
    self._cooling_set_point_schedules = value
