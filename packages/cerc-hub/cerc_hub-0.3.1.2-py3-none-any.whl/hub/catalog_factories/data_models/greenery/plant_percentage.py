"""
Greenery catalog data model Plant percentage class
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.catalog_factories.data_models.greenery.plant import Plant as HubPlant


class PlantPercentage(HubPlant):
  """
  Plant percentage class
  """

  def __init__(self, percentage, plant_category, plant):
    super().__init__(plant_category, plant)
    self._percentage = percentage

  @property
  def percentage(self):
    """
    Get plant percentage
    :return: float
    """
    return self._percentage

  def to_dictionary(self):
    """Class content to dictionary"""
    _soils = []
    for _soil in self.grows_on:
      _soils.append(_soil.to_dictionary())
    content = {'Plant': {'name': self.name,
                         'percentage': self.percentage,
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
