"""
Sensor module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.helpers.location import Location
from hub.city_model_structure.iot.sensor_measure import SensorMeasure
from hub.city_model_structure.iot.sensor_type import SensorType


class Sensor:
  """
  Sensor abstract class
  """
  def __init__(self):
    self._name = None
    self._type = None
    self._units = None
    self._location = None

  @property
  def name(self):
    """
    Get sensor name
    :return: str
    """
    if self._name is None:
      raise ValueError('Undefined sensor name')
    return self._name

  @name.setter
  def name(self, value):
    """
    Set sensor name
    :param value: str
    """
    if value is not None:
      self._name = str(value)

  @property
  def type(self) -> SensorType:
    """
    Get sensor type
    :return: str
    """
    return self._type

  @property
  def units(self):
    """
    Get sensor units
    :return: str
    """
    return self._units

  @property
  def location(self) -> Location:
    """
    Get sensor location
    :return: Location
    """
    return self._location

  @location.setter
  def location(self, value):
    """
    Set sensor location
    :param value: Location
    """
    self._location = value

  @property
  def measures(self) -> [SensorMeasure]:
    """
    Raises not implemented error
    """
    raise NotImplementedError
