"""
Ecoinvent CO2 Emissions Catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""
import json
from pathlib import Path

from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.co2_analysis.content import Content
from hub.catalog_factories.data_models.co2_analysis.embodied_co2_window import EmbodiedCo2Window
from hub.catalog_factories.data_models.co2_analysis.embodied_co2_material import EmbodiedCo2Material
from hub.catalog_factories.data_models.co2_analysis.end_of_life_co2_window import EndOfLifeCo2Window
from hub.catalog_factories.data_models.co2_analysis.end_of_life_co2_material import EndOfLifeCo2Material


class EcoinventCatalog(Catalog):
  """
  EcoinventCatalog CO2 emissions catalog class
  """

  def __init__(self, path):
    _path_ecoinvent_co2_emissions = Path(path / 'ecoinvent_co2_analysis.json').resolve()
    with open(_path_ecoinvent_co2_emissions, 'r', encoding='utf-8') as file:
      self._ecoinvent_co2_emissions = json.load(file)

    self._catalog_embodied_co2_windows = self._load_embodied_co2_windows()
    self._catalog_embodied_co2_materials = self._load_embodied_co2_materials()
    self._catalog_end_of_life_co2_windows = self._load_end_of_life_co2_windows()
    self._catalog_end_of_life_co2_materials = self._load_end_of_life_co2_materials()

    self._content = Content(self._catalog_embodied_co2_materials,
                            self._catalog_embodied_co2_windows,
                            self._catalog_end_of_life_co2_materials,
                            self._catalog_end_of_life_co2_windows)

  def _load_embodied_co2_windows(self):
    """
    Populate embodied_co2_windows with values from the catalog
    :return: dict
    """
    _catalog_embodied_co2_windows = []
    embodied_co2_windows = self._ecoinvent_co2_emissions['embodied_co2']['windows']
    for key, embodied_co2_window_values in embodied_co2_windows.items():
      name = key
      embodied_carbon = embodied_co2_window_values['embodied_carbon']
      density = embodied_co2_window_values['density']
      _catalog_embodied_co2_windows.append(EmbodiedCo2Window(name, embodied_carbon, density))
    return _catalog_embodied_co2_windows

  def _load_embodied_co2_materials(self):
    """
    Populate embodied_co2_materials with values from the catalog
    :return: dict
    """
    _catalog_embodied_co2_materials = []
    embodied_co2_materials = self._ecoinvent_co2_emissions['embodied_co2']['materials']
    for key, embodied_co2_material_values in embodied_co2_materials.items():
      name = key
      embodied_carbon = embodied_co2_material_values['embodied_carbon']
      _catalog_embodied_co2_materials.append(EmbodiedCo2Material(name, embodied_carbon))
    return _catalog_embodied_co2_materials

  def _load_end_of_life_co2_windows(self):
    """
    Populate end_of_life_co2_windows with values from the catalog
    :return: dict
    """
    _catalog_end_of_life_co2_windows = []
    end_of_life_co2_windows = self._ecoinvent_co2_emissions['end_of_life_co2']['windows']
    for key, end_of_life_co2_window_values in end_of_life_co2_windows.items():
      name = key
      companies_recycling_machine_emission = end_of_life_co2_window_values['companies_recycling_machine_emission']
      company_recycling_ratio = end_of_life_co2_window_values['company_recycling_ratio']
      demolition_machine_emission = end_of_life_co2_window_values['demolition_machine_emission']
      density = end_of_life_co2_window_values['density']
      landfilling_machine_emission = end_of_life_co2_window_values['landfilling_machine_emission']
      landfilling_ratio = end_of_life_co2_window_values['landfilling_ratio']
      onsite_machine_emission = end_of_life_co2_window_values['onsite_machine_emission']
      onsite_recycling_ratio = end_of_life_co2_window_values['onsite_recycling_ratio']
      recycling_ratio = end_of_life_co2_window_values['recycling_ratio']
      _catalog_end_of_life_co2_windows.append(EndOfLifeCo2Window(name,
                                                                 recycling_ratio,
                                                                 onsite_recycling_ratio,
                                                                 company_recycling_ratio,
                                                                 landfilling_ratio,
                                                                 density,
                                                                 demolition_machine_emission,
                                                                 onsite_machine_emission,
                                                                 companies_recycling_machine_emission,
                                                                 landfilling_machine_emission))
    return _catalog_end_of_life_co2_windows

  def _load_end_of_life_co2_materials(self):
    """
    Populate end_of_life_co2_materials with values from the catalog
    :return: dict
    """
    _catalog_end_of_life_co2_materials = []
    end_of_life_co2_materials = self._ecoinvent_co2_emissions['end_of_life_co2']['materials']
    for key, end_of_life_co2_material_values in end_of_life_co2_materials.items():
      name = key
      recycling_ratio = end_of_life_co2_material_values['recycling_ratio']
      onsite_recycling_ratio = end_of_life_co2_material_values['onsite_recycling_ratio']
      company_recycling_ratio = end_of_life_co2_material_values['company_recycling_ratio']
      landfilling_ratio = end_of_life_co2_material_values['landfilling_ratio']
      demolition_machine_emission = end_of_life_co2_material_values['demolition_machine_emission']
      onsite_machine_emission = end_of_life_co2_material_values['onsite_machine_emission']
      companies_recycling_machine_emission = end_of_life_co2_material_values['companies_recycling_machine_emission']
      landfilling_machine_emission = end_of_life_co2_material_values['landfilling_machine_emission']
      _catalog_end_of_life_co2_materials.append(EndOfLifeCo2Material(name,
                                                                     recycling_ratio,
                                                                     onsite_recycling_ratio,
                                                                     company_recycling_ratio,
                                                                     landfilling_ratio,
                                                                     demolition_machine_emission,
                                                                     onsite_machine_emission,
                                                                     companies_recycling_machine_emission,
                                                                     landfilling_machine_emission))
    return _catalog_end_of_life_co2_materials

  def names(self, category=None):
    """
    Get the catalog elements names
    :parm: optional category filter
    """
    if category is None:
      _names = {'embodied_co2_windows': [],
                'embodied_co2_materials': [],
                'end_of_life_co2_windows': [],
                'end_of_life_co2_materials': []}
      for window in self._content.embodied_co2_window:
        _names['embodied_co2_windows'].append(window.name)
      for material in self._content.embodied_co2_material:
        _names['embodied_co2_materials'].append(material.name)
      for window in self._content.end_of_life_co2_window:
        _names['end_of_life_co2_windows'].append(window.name)
      for material in self._content.end_of_life_co2_material:
        _names['end_of_life_co2_materials'].append(material.name)
    else:
      _names = {category: []}
      if category.lower() == 'embodied_co2_windows':
        for window in self._content.embodied_co2_window:
          _names[category].append(window.name)
      elif category.lower() == 'embodied_co2_materials':
        for material in self._content.embodied_co2_material:
          _names[category].append(material.name)
      elif category.lower() == 'end_of_life_co2_windows':
        for window in self._content.end_of_life_co2_window:
          _names[category].append(window.name)
      elif category.lower() == 'end_of_life_co2_materials':
        for material in self._content.end_of_life_co2_material:
          _names[category].append(material.name)
      else:
        raise ValueError(f'Unknown category [{category}]')
    return _names

  def entries(self, category=None):
    """
    Get the catalog elements
    :parm: optional category filter
    """
    if category is None:
      return self._content
    if category.lower() == 'embodied_co2_windows':
      embodied_co2_windows = []
      for window in self._content.embodied_co2_window:
        embodied_co2_windows.append(window.to_dictionary())
      return embodied_co2_windows
    if category.lower() == 'embodied_co2_materials':
      embodied_co2_materials = []
      for material in self._content.embodied_co2_material:
        embodied_co2_materials.append(material.to_dictionary())
      return embodied_co2_materials
    if category.lower() == 'end_of_life_co2_windows':
      end_of_life_co2_windows = []
      for window in self._content.end_of_life_co2_window:
        end_of_life_co2_windows.append(window.to_dictionary())
      return end_of_life_co2_windows
    if category.lower() == 'end_of_life_co2_materials':
      end_of_life_co2_materials = []
      for material in self._content.end_of_life_co2_material:
        end_of_life_co2_materials.append(material.to_dictionary())
      return end_of_life_co2_materials
    raise ValueError(f'Unknown category [{category}]')

  def get_entry(self, name):
    """
    Get catalog elements by name
    :parm: entry name
    """
    entries = []
    for entry in self._content.embodied_co2_window:
      if entry.name.lower() == name.lower():
        entries.append(entry.to_dictionary())
    for entry in self._content.embodied_co2_material:
      if entry.name.lower() == name.lower():
        entries.append(entry.to_dictionary())
    for entry in self._content.end_of_life_co2_window:
      if entry.name.lower() == name.lower():
        entries.append(entry.to_dictionary())
    for entry in self._content.end_of_life_co2_material:
      if entry.name.lower() == name.lower():
        entries.append( entry.to_dictionary())
    if entries:
      return entries
    raise IndexError(f"{name} doesn't exists in the catalog")
