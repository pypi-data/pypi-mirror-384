"""
Plant module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List
from hub.city_model_structure.greenery.soil import Soil


class Plant:
  """
  Plant class
  """
  def __init__(self, name, height, leaf_area_index, leaf_reflectivity, leaf_emissivity, minimal_stomatal_resistance,
               co2_sequestration, grows_on_soils):
    self._name = name
    self._percentage = None
    self._height = height
    self._leaf_area_index = leaf_area_index
    self._leaf_reflectivity = leaf_reflectivity
    self._leaf_emissivity = leaf_emissivity
    self._minimal_stomatal_resistance = minimal_stomatal_resistance
    self._co2_sequestration = co2_sequestration
    self._grows_on = grows_on_soils

  @property
  def name(self):
    """
    Get plant name
    :return: string
    """
    return self._name

  @property
  def percentage(self):
    """
    Get percentage of plant in vegetation
    :return: float
    """
    return self._percentage

  @percentage.setter
  def percentage(self, value):
    """
    Set percentage of plant in vegetation
    :param value: float
    """
    self._percentage = value

  @property
  def height(self):
    """
    Get plant height in m
    :return: float
    """
    return self._height

  @property
  def leaf_area_index(self):
    """
    Get plant leaf area index
    :return: float
    """
    return self._leaf_area_index

  @property
  def leaf_reflectivity(self):
    """
    Get plant leaf area index
    :return: float
    """
    return self._leaf_reflectivity

  @property
  def leaf_emissivity(self):
    """
    Get plant leaf emissivity
    :return: float
    """
    return self._leaf_emissivity

  @property
  def minimal_stomatal_resistance(self):
    """
    Get plant minimal stomatal resistance in s/m
    :return: float
    """
    return self._minimal_stomatal_resistance

  @property
  def co2_sequestration(self):
    """
    Get plant co2 sequestration capacity in kg CO2 equivalent
    :return: float
    """
    return self._co2_sequestration

  @property
  def grows_on(self) -> List[Soil]:
    """
    Get plant compatible soils
    :return: [Soil]
    """
    return self._grows_on
