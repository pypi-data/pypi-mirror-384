"""
Storey module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from __future__ import annotations
from typing import List
from hub.city_model_structure.building_demand.surface import Surface
from hub.city_model_structure.building_demand.thermal_boundary import ThermalBoundary
from hub.city_model_structure.building_demand.thermal_zone import ThermalZone


class Storey:
  """
  Storey class
  """
  def __init__(self, name, storey_surfaces, neighbours, volume, internal_zone, floor_area):
    self._name = name
    self._storey_surfaces = storey_surfaces
    self._thermal_boundaries = None
    self._virtual_surfaces = None
    self._thermal_zone = None
    self._neighbours = neighbours
    self._volume = volume
    self._internal_zone = internal_zone
    self._floor_area = floor_area

  @property
  def name(self):
    """
    Get storey's name
    :return: str
    """
    return self._name

  @property
  def surfaces(self) -> List[Surface]:
    """
    Get external surfaces enclosing the storey
    :return: [Surface]
    """
    return self._storey_surfaces

  @property
  def neighbours(self):
    """
    Get the neighbour storeys' names
    :return: [str]
    """
    return self._neighbours

  @property
  def thermal_boundaries(self) -> List[ThermalBoundary]:
    """
    Get the thermal boundaries bounding the thermal zone
    :return: [ThermalBoundary]
    """
    if self._thermal_boundaries is None:
      self._thermal_boundaries = []
      for surface in self.surfaces:
        if surface.holes_polygons is None:
          windows_areas = None
        else:
          windows_areas = []
          for hole in surface.holes_polygons:
            windows_areas.append(hole.area)
        new_thermal_boundary = ThermalBoundary(surface, surface.solid_polygon.area, windows_areas)
        surface.associated_thermal_boundaries.append(new_thermal_boundary)
        self._thermal_boundaries.append(new_thermal_boundary)
    return self._thermal_boundaries

  @property
  def virtual_surfaces(self) -> List[Surface]:
    """
    Get the internal surfaces enclosing the thermal zone
    :return: [Surface]
    """
    if self._virtual_surfaces is None:
      self._virtual_surfaces = []
      for thermal_boundary in self.thermal_boundaries:
        self._virtual_surfaces.append(thermal_boundary.internal_surface)
    return self._virtual_surfaces

  @property
  def thermal_zone(self) -> ThermalZone:
    """
    Get the thermal zone inside the storey
    :return: ThermalZone
    """
    if self._thermal_zone is None:
      _number_of_storeys = 1
      self._thermal_zone = ThermalZone(self.thermal_boundaries, self._internal_zone,
                                       self.volume, self.floor_area, _number_of_storeys)
    return self._thermal_zone

  @property
  def volume(self):
    """
    Get storey's volume in cubic meters
    :return: float
    """
    return self._volume

  @property
  def floor_area(self):
    """
    Get storey's floor area in square meters
    :return: float
    """
    return self._floor_area
