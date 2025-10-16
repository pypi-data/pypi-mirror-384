import hub.helpers.constants as cte
from hub.city_model_structure.attributes.polygon import Polygon
from hub.city_model_structure.building import Building
from hub.city_model_structure.building_demand.surface import Surface
from hub.helpers.geometry_helper import GeometryHelper
from hub.imports.geometry.geojson_classes.geojson_base import GeoJsonBase
from hub.imports.geometry.helpers.geometry_helper import GeometryHelper as igh


class GeoJsonLOD0(GeoJsonBase):
  def __init__(self, transformer):
    self._transformer = transformer

  def _add_polygon(self, polygon_coordinates, surfaces):
    points = igh.points_from_string(
      igh.remove_last_point_from_string(
        self._polygon_coordinates_to_3d(polygon_coordinates, self._transformer)
      )
    )
    points = igh.invert_points(points)
    polygon = Polygon(points)
    polygon.area = igh.ground_area(points)
    surface = Surface(polygon, polygon)
    if surface.type == cte.GROUND:
      surfaces.append(surface)
    else:
      distance = cte.MAX_FLOAT
      hole_connect = 0
      surface_connect = 0
      for hole_index, hole_coordinate in enumerate(polygon.coordinates):
        for surface_index, ground_coordinate in enumerate(surfaces[-1].solid_polygon.coordinates):
          current_distance = GeometryHelper.distance_between_points(hole_coordinate, ground_coordinate)
          if current_distance < distance:
            distance = current_distance
            hole_connect = hole_index
            surface_connect = surface_index

      hole = polygon.coordinates[hole_connect:] + polygon.coordinates[:hole_connect] + [
        polygon.coordinates[hole_connect]]
      prefix_coordinates = surfaces[-1].solid_polygon.coordinates[:surface_connect + 1]
      trail_coordinates = surfaces[-1].solid_polygon.coordinates[surface_connect:]
      coordinates = prefix_coordinates + hole + trail_coordinates
      polygon = Polygon(coordinates)
      polygon.area = igh.ground_area(coordinates)
      surfaces[-1] = Surface(polygon, polygon)

  def _parse_polygon(self, coordinates, building_name, building_aliases, function, usages, year_of_construction):
    surfaces = []
    for polygon_coordinates in coordinates:
      self._add_polygon(polygon_coordinates, surfaces)
    building = Building(f'{building_name}', surfaces, year_of_construction, function, usages=usages)
    for alias in building_aliases:
      building.add_alias(alias)
    return building

  def _parse_multi_polygon(self, polygons_coordinates, building_name, building_aliases, function, usages,
                           year_of_construction):
    surfaces = []
    for coordinates in polygons_coordinates:
      for polygon_coordinates in coordinates:
        self._add_polygon(polygon_coordinates, surfaces)
    building = Building(f'{building_name}', surfaces, year_of_construction, function, usages=usages)
    for alias in building_aliases:
      building.add_alias(alias)
    return building

  def parse(self, geometry, building_name, building_aliases, function, usages, year_of_construction):
    if str(geometry['type']).lower() == 'polygon':
      building = self._parse_polygon(geometry['coordinates'], building_name, building_aliases, function, usages, year_of_construction)
    elif str(geometry['type']).lower() == 'multipolygon':
      building = self._parse_multi_polygon(geometry['coordinates'], building_name, building_aliases, function, usages, year_of_construction)
    else:
      raise NotImplementedError(f'Geojson geometry type [{geometry["type"]}] unknown for LOD0')
    building.storeys_above_ground = 0
    return building
