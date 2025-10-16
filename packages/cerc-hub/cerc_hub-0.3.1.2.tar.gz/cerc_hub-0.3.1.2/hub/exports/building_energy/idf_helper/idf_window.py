import logging

import hub.exports.building_energy.idf_helper as idf_cte
import hub.helpers.constants as cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfWindow(IdfBase):

  @staticmethod
  def _to_window_surface(cerc_idf, surface):
    window_ratio = surface.associated_thermal_boundaries[0].window_ratio
    x = 0
    y = 1
    z = 2
    coordinates = cerc_idf.matrix_to_list(surface.solid_polygon.coordinates, cerc_idf.city.lower_corner)
    min_z = surface.lower_corner[z]
    max_z = surface.upper_corner[z]
    middle = (max_z - min_z) / 2
    distance = (max_z - min_z) * window_ratio
    new_max_z = middle + distance / 2
    new_min_z = middle - distance / 2
    for index, coordinate in enumerate(coordinates):
      if coordinate[z] == max_z:
        coordinates[index] = (coordinate[x], coordinate[y], new_max_z)
      elif coordinate[z] == min_z:
        coordinates[index] = (coordinate[x], coordinate[y], new_min_z)
      else:
         logging.warning('Z coordinate not in top or bottom during window creation')
    return coordinates

  @staticmethod
  def add(cerc_idf, building):
    file = cerc_idf.files['fenestration']
    for storey, thermal_zone in enumerate(building.thermal_zones_from_internal_zones):
      for index, boundary in enumerate(thermal_zone.thermal_boundaries):
        building_surface_name = f'Building_{building.name}_storey_{storey}_surface_{index}'
        is_exposed = boundary.parent_surface.type == cte.WALL
        if boundary.parent_surface.percentage_shared is not None and boundary.parent_surface.percentage_shared > 0.5 or boundary.window_ratio == 0:
          is_exposed = False
        if not is_exposed:
          continue
        name = f'Building_{building.name}_storey_{storey}_window_{index}'
        construction_name = f'{boundary.construction_name}_window_construction'
        cerc_idf.write_to_idf_format(file, idf_cte.WINDOW_SURFACE)
        cerc_idf.write_to_idf_format(file, name, 'Name')
        cerc_idf.write_to_idf_format(file, 'Window', 'Surface Type')
        cerc_idf.write_to_idf_format(file, construction_name, 'Construction Name')
        cerc_idf.write_to_idf_format(file, building_surface_name, 'Building Surface Name')
        cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Outside Boundary Condition Object')
        cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'View Factor to Ground')
        cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Frame and Divider Name')
        cerc_idf.write_to_idf_format(file, '1.0', 'Multiplier')
        cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'Number of Vertices')
        coordinates = IdfWindow._to_window_surface(cerc_idf, boundary.parent_surface)
        eol = ','
        coordinates_length = len(coordinates)
        for i, coordinate in enumerate(coordinates):
          vertex = i + 1
          if vertex == coordinates_length:
            eol = ';'
          cerc_idf.write_to_idf_format(file, coordinate[0], f'Vertex {vertex} Xcoordinate')
          cerc_idf.write_to_idf_format(file, coordinate[1], f'Vertex {vertex} Ycoordinate')
          cerc_idf.write_to_idf_format(file, coordinate[2], f'Vertex {vertex} Zcoordinate', eol)
