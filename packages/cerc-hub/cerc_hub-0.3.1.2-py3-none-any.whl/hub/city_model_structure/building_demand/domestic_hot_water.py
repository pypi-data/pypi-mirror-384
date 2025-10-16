"""
Domestic Hot Water module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from typing import Union, List
from hub.city_model_structure.attributes.schedule import Schedule


class DomesticHotWater:
  """
  DomesticHotWater class
  """
  def __init__(self):
    self._density = None
    self._peak_flow = None
    self._service_temperature = None
    self._schedules = None

  @property
  def density(self) -> Union[None, float]:
    """
    Get domestic hot water load density in Watts per m2
    :return: None or float
    """
    return self._density

  @density.setter
  def density(self, value):
    """
    Set domestic hot water load density in Watts per m2
    :param value: float
    """
    if value is not None:
      self._density = float(value)

  @property
  def peak_flow(self) -> Union[None, float]:
    """
    Get domestic hot water peak_flow density in m3 per second and m2
    :return: None or float
    """
    return self._peak_flow

  @peak_flow.setter
  def peak_flow(self, value):
    """
    Set domestic hot water peak_flow density in m3 per second and m2
    :return: None or float
    """
    self._peak_flow = value

  @property
  def service_temperature(self) -> Union[None, float]:
    """
    Get service temperature in degrees Celsius
    :return: None or float
    """
    return self._service_temperature

  @service_temperature.setter
  def service_temperature(self, value):
    """
    Set service temperature in degrees Celsius
    :param value: float
    """
    if value is not None:
      self._service_temperature = float(value)

  @property
  def schedules(self) -> Union[None, List[Schedule]]:
    """
    Get schedules
    dataType = fraction
    :return: None or [Schedule]
    """
    return self._schedules

  @schedules.setter
  def schedules(self, value):
    """
    Set schedules
    dataType = fraction
    :param value: [Schedule]
    """
    self._schedules = value
