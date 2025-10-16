"""
Obj module parses obj files and import the geometry into the city model structure
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
import trimesh.exchange.load
from trimesh import Scene
import trimesh.geometry
from hub.city_model_structure.city import City
from hub.city_model_structure.building import Building
from hub.city_model_structure.building_demand.surface import Surface
from hub.city_model_structure.attributes.polygon import Polygon


class Obj:
  """
  Obj class
  """
  def __init__(self, path):
    self._city = None
    with open(path, 'r', encoding='utf8') as file:
      self._scene = trimesh.exchange.load.load(file, file_type='obj', force='scene')
    self._corners = self._scene.bounds_corners
    _bound_corner_min = None
    _bound_corner_max = None
    for corner in self._corners:
      if _bound_corner_min is None:
        _bound_corner_min = corner
      elif _bound_corner_max is None:
        _bound_corner_max = corner
      else:
        _bound_corner_min[0] = min(_bound_corner_min[0], corner[0])
        _bound_corner_min[1] = min(_bound_corner_min[1], corner[1])
        _bound_corner_min[2] = min(_bound_corner_min[2], corner[2])
        _bound_corner_max[0] = max(_bound_corner_max[0], corner[0])
        _bound_corner_max[1] = max(_bound_corner_max[1], corner[1])
        _bound_corner_max[2] = max(_bound_corner_max[2], corner[2])
    self._lower_corner = _bound_corner_min
    self._upper_corner = _bound_corner_max

  @property
  def scene(self) -> Scene:
    """
    Get obj scene
    """
    return self._scene

  @property
  def city(self) -> City:
    """
    Get city out of an obj file
    """
    lod = 0
    if self._city is None:
      # todo: refactor this method to clearly choose the obj type
      # todo: where do we get this information from?
      srs_name = 'EPSG:26911'

      self._city = City(self._lower_corner, self._upper_corner, srs_name)
      scene = self.scene.geometry
      keys = scene.keys()
      for key in keys:
        name = key
        # todo: where do we get this information from?
        lod = 1
        year_of_construction = 0
        function = ''

        obj = scene[key]
        surfaces = []
        for face in obj.faces:
          points = []
          for vertex_index in face:
            points.append(obj.vertices[vertex_index])
          solid_polygon = Polygon(points)
          perimeter_polygon = solid_polygon
          surface = Surface(solid_polygon, perimeter_polygon)
          surfaces.append(surface)
        building = Building(name, surfaces, year_of_construction, function, terrains=None)
        self._city.add_city_object(building)
      self._city.level_of_detail.geometry = lod
      for building in self._city.buildings:
        building.level_of_detail.geometry = lod

    return self._city
