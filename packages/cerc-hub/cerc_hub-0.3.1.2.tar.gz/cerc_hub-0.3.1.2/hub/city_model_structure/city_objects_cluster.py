"""
CityObjectsCluster module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from abc import ABC
from typing import List
from hub.city_model_structure.iot.sensor import Sensor
from hub.city_model_structure.city_object import CityObject


class CityObjectsCluster(ABC, CityObject):
  """
  CityObjectsCluster(ABC) class
  """
  def __init__(self, name, cluster_type, city_objects):
    self._name = name
    self._cluster_type = cluster_type
    self._city_objects = city_objects
    self._sensors = []
    super().__init__(name, None)

  @property
  def name(self):
    """
    Get cluster name
    :return: str
    """
    return self._name

  @property
  def type(self):
    """
    raises not implemented error
    """
    raise NotImplementedError

  @property
  def city_objects(self):
    """
    raises not implemented error
    """
    raise NotImplementedError

  def add_city_object(self, city_object) -> List[CityObject]:
    """
    add new object to the cluster
    :return: [CityObjects]
    """
    if self._city_objects is None:
      self._city_objects = [city_object]
    else:
      self._city_objects.append(city_object)
    return self._city_objects

  @property
  def sensors(self) -> List[Sensor]:
    """
    Get sensors belonging to the city objects cluster
    :return: [Sensor]
    """
    return self._sensors

  @sensors.setter
  def sensors(self, value):
    """
    Set sensors belonging to the city objects cluster
    :param value: [Sensor]
    """
    self._sensors = value
