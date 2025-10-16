"""
Nrel construction catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from pathlib import Path
import xmltodict
from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.construction.window import Window
from hub.catalog_factories.data_models.construction.material import Material
from hub.catalog_factories.data_models.construction.layer import Layer
from hub.catalog_factories.data_models.construction.construction import Construction
from hub.catalog_factories.data_models.construction.content import Content
from hub.catalog_factories.data_models.construction.archetype import Archetype
from hub.catalog_factories.construction.construction_helper import ConstructionHelper
import hub.helpers.constants as cte


class NrelCatalog(Catalog):
  """
  Nrel catalog class
  """
  def __init__(self, path):
    archetypes_path = str(Path(path / 'us_archetypes.xml').resolve())
    constructions_path = str(Path(path / 'us_constructions.xml').resolve())
    with open(constructions_path, 'r', encoding='utf-8') as xml:
      self._constructions = xmltodict.parse(xml.read(), force_list=('material', 'window', 'construction', 'layer'))
    with open(archetypes_path, 'r', encoding='utf-8') as xml:
      self._archetypes = xmltodict.parse(xml.read(), force_list=('archetype', 'construction'))
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
    windows = self._constructions['library']['windows']['window']
    for window in windows:
      frame_ratio = float(window['frame_ratio']['#text'])
      g_value = window['shgc']
      overall_u_value = float(window['conductivity']['#text']) / float(window['thickness']['#text'])
      name = window['@name']
      window_id = window['@id']
      _catalog_windows.append(Window(window_id, frame_ratio, g_value, overall_u_value, name))
    return _catalog_windows

  def _load_materials(self):
    _catalog_materials = []
    materials = self._constructions['library']['materials']['material']
    for material in materials:
      material_id = material['@id']
      name = material['@name']
      solar_absorptance = float(material['solar_absorptance']['#text'])
      thermal_absorptance = float(material['thermal_absorptance']['#text'])
      visible_absorptance = float(material['visible_absorptance']['#text'])
      no_mass = False
      thermal_resistance = None
      conductivity = None
      density = None
      specific_heat = None
      if 'no_mass' in material and material['no_mass'] == 'true':
        no_mass = True
        thermal_resistance = float(material['thermal_resistance']['#text'])
      else:
        conductivity = float(material['conductivity']['#text'])
        density = float(material['density']['#text'])
        specific_heat = float(material['specific_heat']['#text'])
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
    constructions = self._constructions['library']['constructions']['construction']
    for construction in constructions:
      construction_id = construction['@id']
      construction_type = ConstructionHelper().nrel_surfaces_types_to_hub_types[construction['@type']]
      name = construction['@name']
      layers = []
      for layer in construction['layers']['layer']:
        layer_id = layer['@id']
        layer_name = layer['@name']
        material_id = layer['material'][0]
        thickness = 0
        if 'thickness' in layer:
          thickness = float(layer['thickness']['#text'])
        for material in self._catalog_materials:
          if str(material_id) == str(material.id):
            layers.append(Layer(layer_id, layer_name, material, thickness))
            break
      _catalog_constructions.append(Construction(construction_id, construction_type, name, layers))
    return _catalog_constructions

  def _load_archetypes(self):
    _catalog_archetypes = []
    archetypes = self._archetypes['archetypes']['archetype']
    for archetype in archetypes:
      archetype_id = archetype['@id']
      function = archetype['@building_type']
      name = f"{function} {archetype['@climate_zone']} {archetype['@reference_standard']}"
      climate_zone = archetype['@climate_zone']
      construction_period = ConstructionHelper().reference_standard_to_construction_period[
        archetype['@reference_standard']
      ]
      average_storey_height = float(archetype['average_storey_height']['#text'])
      thermal_capacity = float(archetype['thermal_capacity']['#text']) * 1000
      extra_loses_due_to_thermal_bridges = float(archetype['extra_loses_due_to_thermal_bridges']['#text'])
      indirect_heated_ratio = float(archetype['indirect_heated_ratio']['#text'])
      infiltration_rate_for_ventilation_system_off = float(
        archetype['infiltration_rate_for_ventilation_system_off']['#text']
      ) / cte.HOUR_TO_SECONDS
      infiltration_rate_for_ventilation_system_on = float(
        archetype['infiltration_rate_for_ventilation_system_on']['#text']
      ) / cte.HOUR_TO_SECONDS

      archetype_constructions = []
      for archetype_construction in archetype['constructions']['construction']:
        for construction in self._catalog_constructions:
          if construction.id == archetype_construction['@id']:
            window_ratio = float(archetype_construction['window_ratio']['#text'])
            window_id = archetype_construction['window']
            _construction = None
            _window = None
            for window in self._catalog_windows:
              if window_id == window.id:
                _window = window
                break
            _construction = Construction(construction.id,
                                         construction.type,
                                         construction.name,
                                         construction.layers,
                                         window_ratio,
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
                                           indirect_heated_ratio,
                                           infiltration_rate_for_ventilation_system_off,
                                           infiltration_rate_for_ventilation_system_on,
                                           0,
                                           0))
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
