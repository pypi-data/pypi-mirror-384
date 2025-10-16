"""
Storeys generation helper
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
import math
import sys
from typing import List

import numpy as np

from hub.city_model_structure.attributes.point import Point
from hub.city_model_structure.attributes.polygon import Polygon
from hub.city_model_structure.building_demand.storey import Storey
from hub.city_model_structure.building_demand.surface import Surface
from hub.city_model_structure.building_demand.thermal_zone import ThermalZone
from hub.helpers import constants as cte


class StoreysGeneration:
  """
  StoreysGeneration
  """
  def __init__(self, building, internal_zone, divide_in_storeys=False):
    self._building = building
    self._internal_zone = internal_zone
    self._thermal_zones = []
    self._divide_in_storeys = divide_in_storeys
    self._floor_area = 0
    for ground in building.grounds:
      self._floor_area += ground.perimeter_polygon.area

  @property
  def thermal_zones(self) -> List[ThermalZone]:
    """
    Get subsections of building trimesh by storey in case of no interiors defined
    :return: [Storey]
    """
    number_of_storeys, height = self._calculate_number_storeys_and_height(self._building.average_storey_height,
                                                                          self._building.eave_height,
                                                                          self._building.storeys_above_ground)

    if not self._divide_in_storeys or number_of_storeys == 1:
      storey = Storey('storey_0', self._building.surfaces, [None, None], self._internal_zone.volume,
                      self._internal_zone, self._floor_area)
      for thermal_boundary in storey.thermal_boundaries:
        if thermal_boundary.type != cte.INTERIOR_WALL or thermal_boundary.type != cte.INTERIOR_SLAB:
          # external thermal boundary -> only one thermal zone
          thermal_zones = [storey.thermal_zone]
        else:
          # internal thermal boundary -> two thermal zones
          grad = np.rad2deg(thermal_boundary.parent_surface.inclination)
          if grad >= 170:
            thermal_zones = [storey.thermal_zone, storey.neighbours[0]]
          else:
            thermal_zones = [storey.neighbours[1], storey.thermal_zone]
        thermal_boundary.thermal_zones = thermal_zones
      return [storey.thermal_zone]

    if number_of_storeys == 0:
      raise ArithmeticError('Number of storeys cannot be 0')

    storeys = []
    surfaces_child_last_storey = []
    rest_surfaces = []

    total_volume = 0
    for i in range(0, number_of_storeys - 1):
      name = 'storey_' + str(i)
      surfaces_child = []
      if i == 0:
        neighbours = [None, 'storey_1']
        for surface in self._building.surfaces:
          if surface.type == cte.GROUND:
            surfaces_child.append(surface)
          else:
            rest_surfaces.append(surface)
      else:
        neighbours = ['storey_' + str(i - 1), 'storey_' + str(i + 1)]
      height_division = self._building.lower_corner[2] + height * (i + 1)
      intersections = []
      for surface in rest_surfaces:
        if surface.type == cte.ROOF:
          if height_division >= surface.upper_corner[2] > height_division - height:
            surfaces_child.append(surface)
          else:
            surfaces_child_last_storey.append(surface)
        else:
          surface_child, rest_surface, intersection = surface.divide(height_division)
          surfaces_child.append(surface_child)
          intersections.extend(intersection)
          if i == number_of_storeys - 2:
            surfaces_child_last_storey.append(rest_surface)
      points = []
      for intersection in intersections:
        points.append(intersection[1])
      coordinates = self._intersections_to_coordinates(intersections)
      polygon = Polygon(coordinates)
      ceiling = Surface(polygon, polygon, surface_type=cte.INTERIOR_SLAB)
      surfaces_child.append(ceiling)
      volume = ceiling.perimeter_area * height
      total_volume += volume
      storeys.append(Storey(name, surfaces_child, neighbours, volume, self._internal_zone, self._floor_area))
    name = 'storey_' + str(number_of_storeys - 1)
    neighbours = ['storey_' + str(number_of_storeys - 2), None]
    volume = self._building.volume - total_volume
    if volume < 0:
      raise ArithmeticError('Error in storeys creation, volume of last storey cannot be lower that 0')
    storeys.append(Storey(name, surfaces_child_last_storey, neighbours, volume, self._internal_zone, self._floor_area))

    for storey in storeys:
      for thermal_boundary in storey.thermal_boundaries:
        if thermal_boundary.type != cte.INTERIOR_WALL or thermal_boundary.type != cte.INTERIOR_SLAB:
          # external thermal boundary -> only one thermal zone
          thermal_zones = [storey.thermal_zone]
        else:
          # internal thermal boundary -> two thermal zones
          grad = np.rad2deg(thermal_boundary.parent_surface.inclination)
          if grad >= 170:
            thermal_zones = [storey.thermal_zone, storey.neighbours[0]]
          else:
            thermal_zones = [storey.neighbours[1], storey.thermal_zone]
        thermal_boundary.thermal_zones = thermal_zones

    for storey in storeys:
      self._thermal_zones.append(storey.thermal_zone)

    return self._thermal_zones

  @staticmethod
  def _calculate_number_storeys_and_height(average_storey_height, eave_height, storeys_above_ground):
    if average_storey_height is None:
      if storeys_above_ground is None or storeys_above_ground <= 0:
        sys.stderr.write('Warning: not enough information to divide building into storeys, '
                         'either number of storeys or average storey height must be provided.\n')
        return 0, 0
      number_of_storeys = int(storeys_above_ground)
      height = eave_height / number_of_storeys
    else:
      height = float(average_storey_height)
      if storeys_above_ground is not None:
        number_of_storeys = int(storeys_above_ground)
      else:
        number_of_storeys = math.floor(float(eave_height) / height) + 1
        last_storey_height = float(eave_height) - height*(number_of_storeys-1)
        if last_storey_height < 0.3*height:
          number_of_storeys -= 1
    return number_of_storeys, height

  @staticmethod
  def _intersections_to_coordinates(edges_list):
    # todo: this method is not robust, the while loop needs to be improved
    points = [Point(edges_list[0][0]), Point(edges_list[0][1])]
    found_edges = []
    j = 0
    while j < len(points)-1:
      for i in range(1, len(edges_list)):
        if i not in found_edges:
          point_2 = points[len(points) - 1]
          point_1 = Point(edges_list[i][0])
          found = False
          if point_1.distance_to_point(point_2) <= 1e-10:
            points.append(Point(edges_list[i][1]))
            found_edges.append(i)
            found = True
          if not found:
            point_1 = Point(edges_list[i][1])
            if point_1.distance_to_point(point_2) <= 1e-10:
              points.append(Point(edges_list[i][0]))
              found_edges.append(i)
      j += 1

    points.remove(points[len(points)-1])
    array_points = []
    for point in points:
      array_points.append(point.coordinates)
    return np.array(array_points)
