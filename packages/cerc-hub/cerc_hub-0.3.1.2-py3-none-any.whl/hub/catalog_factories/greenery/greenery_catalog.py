"""
Greenery catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from pathlib import Path
from pyecore.resources import ResourceSet, URI
from hub.catalog_factories.greenery.ecore_greenery.greenerycatalog import GreeneryCatalog as Gc
from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.greenery.vegetation import Vegetation as HubVegetation
from hub.catalog_factories.data_models.greenery.plant import Plant as HubPlant
from hub.catalog_factories.data_models.greenery.soil import Soil as HubSoil
from hub.catalog_factories.data_models.greenery.plant_percentage import PlantPercentage as HubPlantPercentage
from hub.catalog_factories.data_models.greenery.content import Content as GreeneryContent


class GreeneryCatalog(Catalog):
  """
  Greenery catalog class
  """

  def __init__(self, path):
    base_path = Path(Path(__file__).parent / 'ecore_greenery/greenerycatalog_no_quantities.ecore').resolve()
    resource_set = ResourceSet()
    data_model = resource_set.get_resource(URI(str(base_path)))
    data_model_root = data_model.contents[0]
    resource_set.metamodel_registry[data_model_root.nsURI] = data_model_root
    resource = resource_set.get_resource(URI(str(path)))
    catalog_data: Gc = resource.contents[0]

    plants = []
    for plant_category in catalog_data.plantCategories:
      name = plant_category.name
      for plant in plant_category.plants:
        plants.append(HubPlant(name, plant))

    vegetations = []
    for vegetation_category in catalog_data.vegetationCategories:
      name = vegetation_category.name
      for vegetation in vegetation_category.vegetationTemplates:
        plant_percentages = []

        for plant_percentage in vegetation.plants:
          plant_category = "Unknown"
          for plant in plants:
            if plant.name == plant_percentage.plant.name:
              plant_category = plant.category
              break
          plant_percentages.append(
            HubPlantPercentage(plant_percentage.percentage, plant_category, plant_percentage.plant)
          )
        vegetations.append(HubVegetation(name, vegetation, plant_percentages))
    plants = []
    for plant_category in catalog_data.plantCategories:
      name = plant_category.name
      for plant in plant_category.plants:
        plants.append(HubPlant(name, plant))

    soils = []
    for soil in catalog_data.soils:
      soils.append(HubSoil(soil))

    self._content = GreeneryContent(vegetations, plants, soils)

  def names(self, category=None):
    """
    Get the catalog elements names
    :parm: optional category filter
    """
    if category is None:
      _names = {'vegetations': [], 'plants': [], 'soils': []}
      for vegetation in self._content.vegetations:
        _names['vegetations'].append(vegetation.name)
      for plant in self._content.plants:
        _names['plants'].append(plant.name)
      for soil in self._content.soils:
        _names['soils'].append(soil.name)
    else:
      _names = {category: []}
      if category.lower() == 'vegetations':
        for vegetation in self._content.vegetations:
          _names[category].append(vegetation.name)
      elif category.lower() == 'plants':
        for plant in self._content.plants:
          _names[category].append(plant.name)
      elif category.lower() == 'soils':
        for soil in self._content.soils:
          _names[category].append(soil.name)
      else:
        raise ValueError(f'Unknown category [{category}]')
    return _names

  def get_entry(self, name):
    """
    Get one complete entry from the greenery catalog
    """
    for entry in self._content.vegetations:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.plants:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.soils:
      if entry.name.lower() == name.lower():
        return entry
    raise IndexError(f"{name} doesn't exists in the catalog")

  def entries(self, category=None):
    """
    Get all entries from the greenery catalog optionally filtered by category
    """
    if category is None:
      return self._content
    if category.lower() == 'vegetations':
      return self._content.vegetations
    if category.lower() == 'plants':
      return self._content.plants
    if category.lower() == 'soils':
      return self._content.soils
    raise ValueError(f'Unknown category [{category}]')
