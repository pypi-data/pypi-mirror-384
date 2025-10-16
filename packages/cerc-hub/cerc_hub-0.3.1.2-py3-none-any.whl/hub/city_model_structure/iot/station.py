"""
Station module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import uuid

from hub.city_model_structure.iot.sensor import Sensor


class Station:
  """
  Station class
  """
  def __init__(self, station_id=None, _mobile=False):
    self._id = station_id
    self._mobile = _mobile
    self._sensors = []

  @property
  def id(self):
    """
    Get the station id a random uuid will be assigned if no ID was provided to the constructor
    :return: ID
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def mobile(self):
    """
    Get if the station is mobile or not
    :return: bool
    """
    return self._mobile

  @property
  def sensors(self) -> [Sensor]:
    """
    Get the sensors belonging to the station
    :return: [Sensor]
    """
    return self._sensors
