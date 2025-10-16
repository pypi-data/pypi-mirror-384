"""
Thermal zones creation module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.imports.construction.helpers.storeys_generation import StoreysGeneration


class ThermalZonesCreation:
  """
  PeakLoads class
  """
  def __init__(self, building=None):
    self._building = building

#  # The agreement is that the layers are defined from outside to inside
#  external_layer = catalog_construction.layers[0]
#  external_surface = thermal_boundary.parent_surface
#  external_surface.short_wave_reflectance = 1 - external_layer.material.solar_absorptance
#  external_surface.long_wave_emittance = 1 - external_layer.material.solar_absorptance
#  internal_layer = catalog_construction.layers[len(catalog_construction.layers) - 1]
#  internal_surface = thermal_boundary.internal_surface
#  internal_surface.short_wave_reflectance = 1 - internal_layer.material.solar_absorptance
#  internal_surface.long_wave_emittance = 1 - internal_layer.material.solar_absorptance

  @property
  def thermal_zones_from_storeys(self):
    """
    Create and get thermal zones as 1 per each storey
    :return: [ThermalZone]
    """
    raise NotImplementedError

  @staticmethod
  def _create_storeys(building, archetype, divide_in_storeys):
    building.average_storey_height = archetype.average_storey_height
    thermal_zones = StoreysGeneration(building, building.internal_zones[0],
                                      divide_in_storeys=divide_in_storeys).thermal_zones
    building.internal_zones[0].thermal_zones_from_internal_zones = thermal_zones
