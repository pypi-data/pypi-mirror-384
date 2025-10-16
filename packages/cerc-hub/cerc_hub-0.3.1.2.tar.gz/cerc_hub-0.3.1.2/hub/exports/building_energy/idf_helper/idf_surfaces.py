import hub.exports.building_energy.idf_helper as idf_cte
import hub.helpers.constants as cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfSurfaces(IdfBase):
  @staticmethod
  def add(cerc_idf, building):
    file = cerc_idf.files['surfaces']
    for storey, thermal_zone in enumerate(building.thermal_zones_from_internal_zones):
      for index, boundary in enumerate(thermal_zone.thermal_boundaries):
        surface_type = idf_cte.idf_surfaces_dictionary[boundary.parent_surface.type]
        outside_boundary_condition = idf_cte.OUTDOORS
        sun_exposure = idf_cte.SUN_EXPOSED
        wind_exposure = idf_cte.WIND_EXPOSED
        outside_boundary_condition_object = idf_cte.EMPTY
        name = f'Building_{building.name}_storey_{storey}_surface_{index}'
        construction_name = f'{boundary.construction_name} {boundary.parent_surface.type}'
        space_name = idf_cte.EMPTY
        if boundary.parent_surface.type == cte.GROUND:
          outside_boundary_condition = idf_cte.GROUND
          sun_exposure = idf_cte.NON_SUN_EXPOSED
          wind_exposure = idf_cte.NON_WIND_EXPOSED
        if boundary.parent_surface.percentage_shared is not None and boundary.parent_surface.percentage_shared > 0.5:
          outside_boundary_condition_object = name
          outside_boundary_condition = idf_cte.SURFACE
          sun_exposure = idf_cte.NON_SUN_EXPOSED
          wind_exposure = idf_cte.NON_WIND_EXPOSED
        cerc_idf.write_to_idf_format(file, idf_cte.BUILDING_SURFACE)
        cerc_idf.write_to_idf_format(file, name, 'Name')
        cerc_idf.write_to_idf_format(file, surface_type, 'Surface Type')
        cerc_idf.write_to_idf_format(file, construction_name, 'Construction Name')
        cerc_idf.write_to_idf_format(file, f'{building.name}_{storey}', 'Zone Name')
        cerc_idf.write_to_idf_format(file, space_name, 'Space Name')
        cerc_idf.write_to_idf_format(file, outside_boundary_condition, 'Outside Boundary Condition')
        cerc_idf.write_to_idf_format(file, outside_boundary_condition_object, 'Outside Boundary Condition Object')
        cerc_idf.write_to_idf_format(file, sun_exposure, 'Sun Exposure')
        cerc_idf.write_to_idf_format(file, wind_exposure, 'Wind Exposure')
        cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'View Factor to Ground')
        cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'Number of Vertices')
        coordinates = cerc_idf.matrix_to_list(boundary.parent_surface.solid_polygon.coordinates,
                                              cerc_idf.city.lower_corner)
        eol = ','
        coordinates_length = len(coordinates)
        for i, coordinate in enumerate(coordinates):
          vertex = i + 1
          if vertex == coordinates_length:
            eol = ';'
          cerc_idf.write_to_idf_format(file, coordinate[0], f'Vertex {vertex} Xcoordinate')
          cerc_idf.write_to_idf_format(file, coordinate[1], f'Vertex {vertex} Ycoordinate')
          cerc_idf.write_to_idf_format(file, coordinate[2], f'Vertex {vertex} Zcoordinate', eol)
