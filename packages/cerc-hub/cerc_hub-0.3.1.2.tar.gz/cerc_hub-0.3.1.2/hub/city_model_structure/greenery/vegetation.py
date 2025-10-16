"""
Vegetation module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List
from hub.city_model_structure.greenery.soil import Soil
from hub.city_model_structure.greenery.plant import Plant


class Vegetation:
  """
  Vegetation class
  """
  def __init__(self, name, soil, soil_thickness, plants):
    self._name = name
    self._management = None
    self._air_gap = None
    self._soil = soil
    self._soil_thickness = soil_thickness
    self._plants = plants

  @property
  def name(self):
    """
    Get vegetation name
    :return: string
    """
    return self._name

  @property
  def management(self):
    """
    Get management
    :return: string
    """
    return self._management

  @management.setter
  def management(self, value):
    """
    Set management
    :param value: string
    """
    self._management = value

  @property
  def air_gap(self):
    """
    Get air gap in m
    :return: float
    """
    return self._air_gap

  @air_gap.setter
  def air_gap(self, value):
    """
    Set air gap in m
    :param value: float
    """
    self._air_gap = value

  @property
  def soil(self) -> Soil:
    """
    Get soil
    :return: Soil
    """
    return self._soil

  @property
  def soil_thickness(self):
    """
    Get soil thickness in m
    :return: float
    """
    return self._soil_thickness

  @property
  def plants(self) -> List[Plant]:
    """
    Get list plants in the vegetation
    :return: List[Plant]
    """
    return self._plants
