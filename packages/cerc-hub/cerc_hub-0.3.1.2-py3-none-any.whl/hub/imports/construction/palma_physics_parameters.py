"""
PalmaPhysicsParameters import the construction and material information defined by Palma
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Cecilia Pérez Pérez cperez@irec.cat
"""
import logging

from hub.catalog_factories.construction_catalog_factory import ConstructionCatalogFactory
from hub.city_model_structure.building_demand.thermal_archetype import ThermalArchetype
from hub.city_model_structure.building_demand.construction import Construction
from hub.city_model_structure.building_demand.layer import Layer
from hub.helpers.dictionaries import Dictionaries
from hub.imports.construction.helpers.construction_helper import ConstructionHelper


class PalmaPhysicsParameters:
  """
  PalmaPhysicsParameters class
  """

  def __init__(self, city, divide_in_storeys=False):
    self._city = city
    self._divide_in_storeys = divide_in_storeys
    self._climate_zone = ConstructionHelper.city_to_palma_climate_zone(city.climate_reference_city)

  def enrich_buildings(self):
    """
    Returns the city with the construction parameters assigned to the buildings
    """
    city = self._city
    palma_catalog = ConstructionCatalogFactory('palma').catalog
    for building in city.buildings:
      if building.function not in Dictionaries().hub_function_to_palma_construction_function:
        logging.error('Building %s has an unknown building function %s', building.name, building.function)
        continue
      function = Dictionaries().hub_function_to_palma_construction_function[building.function]
      try:
        archetype = self._search_archetype(palma_catalog, function, building.year_of_construction, self._climate_zone)

      except KeyError:
        logging.error('Building %s has unknown construction archetype for building function: %s '
                      '[%s], building year of construction: %s and climate zone %s', building.name, function,
                      building.function, building.year_of_construction, self._climate_zone)
        continue
      thermal_archetype = ThermalArchetype()
      self._assign_values(thermal_archetype, archetype)
      for internal_zone in building.internal_zones:
        if internal_zone.thermal_archetype is not None:
          thermal_archetype.average_storey_height = internal_zone.thermal_archetype.average_storey_height
        internal_zone.thermal_archetype = thermal_archetype

  @staticmethod
  def _search_archetype(nrcan_catalog, function, year_of_construction, climate_zone):
    nrcan_archetypes = nrcan_catalog.entries('archetypes')
    for building_archetype in nrcan_archetypes:
      construction_period_limits = building_archetype.construction_period.split('_')
      if int(construction_period_limits[0]) <= int(year_of_construction) <= int(construction_period_limits[1]):
        if str(function) == str(building_archetype.function) and climate_zone == str(building_archetype.climate_zone):
          return building_archetype
    raise KeyError('archetype not found')

  @staticmethod
  def _assign_values(thermal_archetype, catalog_archetype):
    thermal_archetype.average_storey_height = catalog_archetype.average_storey_height
    thermal_archetype.extra_loses_due_to_thermal_bridges = catalog_archetype.extra_loses_due_to_thermal_bridges
    thermal_archetype.thermal_capacity = catalog_archetype.thermal_capacity
    thermal_archetype.indirect_heated_ratio = 0
    thermal_archetype.infiltration_rate_for_ventilation_system_on = catalog_archetype.infiltration_rate_for_ventilation_system_on
    thermal_archetype.infiltration_rate_for_ventilation_system_off = catalog_archetype.infiltration_rate_for_ventilation_system_off
    thermal_archetype.infiltration_rate_area_for_ventilation_system_on = catalog_archetype.infiltration_rate_area_for_ventilation_system_on
    thermal_archetype.infiltration_rate_area_for_ventilation_system_off = catalog_archetype.infiltration_rate_area_for_ventilation_system_off
    _constructions = []
    for catalog_construction in catalog_archetype.constructions:
      construction = Construction()
      construction.type = catalog_construction.type
      construction.name = catalog_construction.name
      if catalog_construction.window_ratio is not None:
        for _orientation in catalog_construction.window_ratio:
          if catalog_construction.window_ratio[_orientation] is None:
            catalog_construction.window_ratio[_orientation] = 0
      construction.window_ratio = catalog_construction.window_ratio
      _layers = []
      for layer_archetype in catalog_construction.layers:
        layer = Layer()
        layer.thickness = layer_archetype.thickness
        archetype_material = layer_archetype.material
        layer.material_name = archetype_material.name
        layer.no_mass = archetype_material.no_mass
        if archetype_material.no_mass:
          layer.thermal_resistance = archetype_material.thermal_resistance
        else:
          layer.density = archetype_material.density
          layer.conductivity = archetype_material.conductivity
          layer.specific_heat = archetype_material.specific_heat
        layer.solar_absorptance = archetype_material.solar_absorptance
        layer.thermal_absorptance = archetype_material.thermal_absorptance
        layer.visible_absorptance = archetype_material.visible_absorptance
        _layers.append(layer)
      construction.layers = _layers

      if catalog_construction.window is not None:
        window_archetype = catalog_construction.window
        construction.window_type = window_archetype.name
        construction.window_frame_ratio = window_archetype.frame_ratio
        construction.window_g_value = window_archetype.g_value
        construction.window_overall_u_value = window_archetype.overall_u_value
      _constructions.append(construction)
    thermal_archetype.constructions = _constructions
