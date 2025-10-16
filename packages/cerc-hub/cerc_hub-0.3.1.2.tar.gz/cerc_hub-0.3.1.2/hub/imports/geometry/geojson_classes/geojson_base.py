"""
GeoJsonBase module abstract class to template the different level of details
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from abc import ABC

from hub.city_model_structure.city import City
from hub.helpers.geometry_helper import GeometryHelper

import hub.helpers.constants as cte


class GeoJsonBase(ABC):
  """
  Geojson base class
  """
  _X = 0
  _Y = 1
  _min_x = cte.MAX_FLOAT
  _min_y = cte.MAX_FLOAT
  _max_x = cte.MIN_FLOAT
  _max_y = cte.MIN_FLOAT
  _max_z = 0

  def _save_bounds(self, x, y):
    self._max_x = max(x, self._max_x)
    self._max_y = max(y, self._max_y)
    self._min_x = min(x, self._min_x)
    self._min_y = min(y, self._min_y)

  @staticmethod
  def _find_wall(line_1, line_2):
    if line_1 == [] or line_2 == []:
      return False
    for i in range(0, 2):
      j = 1 - i
      point_1 = line_1[i]
      point_2 = line_2[j]
      distance = GeometryHelper.distance_between_points(point_1, point_2)
      if distance > 1e-2:
        return False
    return True

  def store_shared_percentage_to_walls(self, city, city_mapped):
    for building in city.buildings:
      if building.name not in city_mapped.keys():
        for wall in building.walls:
          wall.percentage_shared = 0
        continue
      building_mapped = city_mapped[building.name]
      for wall in building.walls:
        percentage = 0
        ground_line = []
        for point in wall.perimeter_polygon.coordinates:
          if point[2] < 0.5:
            ground_line.append(point)
        for entry in building_mapped:
          if building_mapped[entry]['shared_points'] <= 2:
            continue
          line = [building_mapped[entry]['line_start'], building_mapped[entry]['line_end']]
          neighbour_line = [building_mapped[entry]['neighbour_line_start'],
                            building_mapped[entry]['neighbour_line_end']]
          neighbour_height = city.city_object(building_mapped[entry]['neighbour_name']).max_height
          if self._find_wall(line, ground_line):
            line_shared = (GeometryHelper.distance_between_points(line[0], line[1]) +
                           GeometryHelper.distance_between_points(neighbour_line[0], neighbour_line[1]) -
                           GeometryHelper.distance_between_points(line[1], neighbour_line[0]) -
                           GeometryHelper.distance_between_points(line[0], neighbour_line[1])) / 2
            percentage_ground = line_shared / GeometryHelper.distance_between_points(line[0], line[1])
            percentage_height = neighbour_height / building.max_height
            percentage_height = min(percentage_height, 1)
            percentage += percentage_ground * percentage_height
        wall.percentage_shared = percentage

  def _polygon_coordinates_to_3d(self, polygon_coordinates, transformer):
    transformed_coordinates = ''
    for coordinate in polygon_coordinates:
      transformed = transformer.transform(coordinate[self._Y], coordinate[self._X])
      self._save_bounds(transformed[self._X], transformed[self._Y])
      transformed_coordinates = f'{transformed_coordinates} {transformed[self._X]} {transformed[self._Y]} 0.0'
    return transformed_coordinates.lstrip(' ')

  @property
  def lower_corner(self):
    return [self._min_x, self._min_y, 0.0]

  @property
  def upper_corner(self):
    return [self._max_x, self._max_y, self._max_z]

  def city(self, hub_crs):
    return City(self.lower_corner, self.upper_corner, hub_crs)
