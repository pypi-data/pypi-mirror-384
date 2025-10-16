"""
Greenery catalog data model Plant class
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.catalog_factories.data_models.greenery.soil import Soil as hub_soil


class Plant:
  """
  Plant class
  """
  def __init__(self, category, plant):
    self._name = plant.name
    self._category = category
    self._height = plant.height
    self._leaf_area_index = plant.leafAreaIndex
    self._leaf_reflectivity = plant.leafReflectivity
    self._leaf_emissivity = plant.leafEmissivity
    self._minimal_stomatal_resistance = plant.minimalStomatalResistance
    self._co2_sequestration = plant.co2Sequestration
    self._grows_on = []
    for soil in plant.growsOn:
      self._grows_on.append(hub_soil(soil))

  @property
  def name(self):
    """
    Get plant name
    :return: string
    """
    return self._name

  @property
  def category(self):
    """
    Get plant category name
    :return: string
    """
    return self._category

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
  def grows_on(self) -> [hub_soil]:
    """
    Get plant compatible soils
    :return: [Soil]
    """
    return self._grows_on

  def to_dictionary(self):
    """Class content to dictionary"""
    _soils = []
    for _soil in self.grows_on:
      _soils.append(_soil.to_dictionary())
    content = {'Plant': {'name': self.name,
                         'category': self.category,
                         'height [m]': self.height,
                         'leaf area index': self.leaf_area_index,
                         'leaf reflectivity': self.leaf_reflectivity,
                         'leaf emissivity': self.leaf_emissivity,
                         'minimal stomatal resistance [s/m]': self.minimal_stomatal_resistance,
                         'co2 sequestration [kg????]': self.co2_sequestration,
                         'soils where it grows on': _soils
                         }
               }

    return content
