"""
NRCAN construction catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import json
from pathlib import Path
from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.construction.content import Content
from hub.catalog_factories.construction.construction_helper import ConstructionHelper
from hub.catalog_factories.data_models.construction.construction import Construction
from hub.catalog_factories.data_models.construction.archetype import Archetype
from hub.catalog_factories.data_models.construction.window import Window
from hub.catalog_factories.data_models.construction.material import Material
from hub.catalog_factories.data_models.construction.layer import Layer
import hub.helpers.constants as cte


class NrcanCatalog(Catalog):
  """
  Nrcan catalog class
  """
  def __init__(self, path):
    _path_archetypes = Path(path / 'nrcan_archetypes.json').resolve()
    _path_constructions = (path / 'nrcan_constructions.json').resolve()
    with open(_path_archetypes, 'r', encoding='utf-8') as file:
      self._archetypes = json.load(file)
    with open(_path_constructions, 'r', encoding='utf-8') as file:
      self._constructions = json.load(file)

    self._catalog_windows = self._load_windows()
    self._catalog_materials = self._load_materials()
    self._catalog_constructions = self._load_constructions()
    self._catalog_archetypes = self._load_archetypes()

    # store the full catalog data model in self._content
    self._content = Content(self._catalog_archetypes,
                            self._catalog_constructions,
                            self._catalog_materials,
                            self._catalog_windows)

  def _load_windows(self):
    _catalog_windows = []
    windows = self._constructions['transparent_surfaces']
    for window in windows:
      name = list(window.keys())[0]
      window_id = name
      g_value = window[name]['shgc']
      window_type = window[name]['type']
      frame_ratio = window[name]['frame_ratio']
      overall_u_value = window[name]['u_value']
      _catalog_windows.append(Window(window_id, frame_ratio, g_value, overall_u_value, name, window_type))
    return _catalog_windows

  def _load_materials(self):
    _catalog_materials = []
    materials = self._constructions['materials']
    for material in materials:
      name = list(material.keys())[0]
      material_id = name
      no_mass = material[name]['no_mass']
      thermal_resistance = None
      conductivity = None
      density = None
      specific_heat = None
      solar_absorptance = None
      thermal_absorptance = None
      visible_absorptance = None
      if no_mass:
        thermal_resistance = material[name]['thermal_resistance']
      else:
        solar_absorptance = material[name]['solar_absorptance']
        thermal_absorptance = str(1 - float(material[name]['thermal_emittance']))
        visible_absorptance = material[name]['visible_absorptance']
        conductivity = material[name]['conductivity']
        density = material[name]['density']
        specific_heat = material[name]['specific_heat']
      _material = Material(material_id,
                           name,
                           solar_absorptance,
                           thermal_absorptance,
                           visible_absorptance,
                           no_mass,
                           thermal_resistance,
                           conductivity,
                           density,
                           specific_heat)
      _catalog_materials.append(_material)
    return _catalog_materials

  def _load_constructions(self):
    _catalog_constructions = []
    constructions = self._constructions['opaque_surfaces']
    for construction in constructions:
      name = list(construction.keys())[0]
      construction_id = name
      construction_type = ConstructionHelper().nrcan_surfaces_types_to_hub_types[construction[name]['type']]
      layers = []
      for layer in construction[name]['layers']:
        layer_id = layer
        layer_name = layer
        material_id = layer
        thickness = construction[name]['layers'][layer]
        for material in self._catalog_materials:
          if str(material_id) == str(material.id):
            layers.append(Layer(layer_id, layer_name, material, thickness))
            break
      _catalog_constructions.append(Construction(construction_id, construction_type, name, layers))
    return _catalog_constructions

  def _load_archetypes(self):
    _catalog_archetypes = []
    archetypes = self._archetypes['archetypes']
    for archetype in archetypes:
      archetype_id = f'{archetype["function"]}_{archetype["period_of_construction"]}_{archetype["climate_zone"]}'
      function = archetype['function']
      name = archetype_id
      climate_zone = archetype['climate_zone']
      construction_period = archetype['period_of_construction']
      average_storey_height = archetype['average_storey_height']
      thermal_capacity = float(archetype['thermal_capacity']) * 1000
      extra_loses_due_to_thermal_bridges = archetype['extra_loses_due_thermal_bridges']
      infiltration_rate_for_ventilation_system_off = (
        archetype['infiltration_rate_for_ventilation_system_off'] / cte.HOUR_TO_SECONDS
      )
      infiltration_rate_for_ventilation_system_on = (
        archetype['infiltration_rate_for_ventilation_system_on'] / cte.HOUR_TO_SECONDS
      )
      infiltration_rate_area_for_ventilation_system_off = (
              archetype['infiltration_rate_area_for_ventilation_system_off'] * 1
      )
      infiltration_rate_area_for_ventilation_system_on = (
              archetype['infiltration_rate_area_for_ventilation_system_on'] * 1
      )

      archetype_constructions = []
      for archetype_construction in archetype['constructions']:
        archetype_construction_type = ConstructionHelper().nrcan_surfaces_types_to_hub_types[archetype_construction]
        archetype_construction_name = archetype['constructions'][archetype_construction]['opaque_surface_name']
        for construction in self._catalog_constructions:
          if archetype_construction_type == construction.type and construction.name == archetype_construction_name:
            _construction = None
            _window = None
            _window_ratio = None
            if 'transparent_surface_name' in archetype['constructions'][archetype_construction].keys():
              _window_ratio = archetype['constructions'][archetype_construction]['transparent_ratio']
              _window_id = archetype['constructions'][archetype_construction]['transparent_surface_name']
              for window in self._catalog_windows:
                if _window_id == window.id:
                  _window = window
                  break
            _construction = Construction(construction.id,
                                         construction.type,
                                         construction.name,
                                         construction.layers,
                                         _window_ratio,
                                         _window)
            archetype_constructions.append(_construction)
            break
      _catalog_archetypes.append(Archetype(archetype_id,
                                           name,
                                           function,
                                           climate_zone,
                                           construction_period,
                                           archetype_constructions,
                                           average_storey_height,
                                           thermal_capacity,
                                           extra_loses_due_to_thermal_bridges,
                                           None,
                                           infiltration_rate_for_ventilation_system_off,
                                           infiltration_rate_for_ventilation_system_on,
                                           infiltration_rate_area_for_ventilation_system_off,
                                           infiltration_rate_area_for_ventilation_system_on
                                           ))
    return _catalog_archetypes

  def names(self, category=None):
    """
    Get the catalog elements names
    :parm: optional category filter
    """
    if category is None:
      _names = {'archetypes': [], 'constructions': [], 'materials': [], 'windows': []}
      for archetype in self._content.archetypes:
        _names['archetypes'].append(archetype.name)
      for construction in self._content.constructions:
        _names['constructions'].append(construction.name)
      for material in self._content.materials:
        _names['materials'].append(material.name)
      for window in self._content.windows:
        _names['windows'].append(window.name)
    else:
      _names = {category: []}
      if category.lower() == 'archetypes':
        for archetype in self._content.archetypes:
          _names[category].append(archetype.name)
      elif category.lower() == 'constructions':
        for construction in self._content.constructions:
          _names[category].append(construction.name)
      elif category.lower() == 'materials':
        for material in self._content.materials:
          _names[category].append(material.name)
      elif category.lower() == 'windows':
        for window in self._content.windows:
          _names[category].append(window.name)
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
    if category.lower() == 'archetypes':
      return self._content.archetypes
    if category.lower() == 'constructions':
      return self._content.constructions
    if category.lower() == 'materials':
      return self._content.materials
    if category.lower() == 'windows':
      return self._content.windows
    raise ValueError(f'Unknown category [{category}]')

  def get_entry(self, name):
    """
    Get one catalog element by names
    :parm: entry name
    """
    for entry in self._content.archetypes:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.constructions:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.materials:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.windows:
      if entry.name.lower() == name.lower():
        return entry
    raise IndexError(f"{name} doesn't exists in the catalog")
