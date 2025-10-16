"""
CityObject module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from __future__ import annotations
from typing import List, Union

from hub.city_model_structure.level_of_detail import LevelOfDetail
from hub.city_model_structure.iot.sensor import Sensor
from hub.city_model_structure.building_demand.surface import Surface
from hub.city_model_structure.attributes.polyhedron import Polyhedron

from hub.helpers.configuration_helper import ConfigurationHelper


class CityObject:
  """
  class CityObject
  """
  def __init__(self, name, surfaces):
    self._name = name
    self._level_of_detail = LevelOfDetail()
    self._surfaces = surfaces
    self._type = None
    self._city_object_lower_corner = None
    self._city_object_upper_corner = None
    self._detailed_polyhedron = None
    self._simplified_polyhedron = None
    self._min_x = ConfigurationHelper().max_coordinate
    self._min_y = ConfigurationHelper().max_coordinate
    self._min_z = ConfigurationHelper().max_coordinate
    self._max_x = ConfigurationHelper().min_coordinate
    self._max_y = ConfigurationHelper().min_coordinate
    self._max_z = ConfigurationHelper().min_coordinate
    self._centroid = None
    self._volume = None
    self._external_temperature = {}
    self._ground_temperature = {}
    self._global_horizontal = {}
    self._diffuse = {}
    self._direct_normal = {}
    self._sensors = []
    self._neighbours = None
    self._beam = {}

  @property
  def level_of_detail(self) -> LevelOfDetail:
    """
    Get level of detail of different aspects of the city: geometry, construction and usage
    :return: LevelOfDetail
    """
    return self._level_of_detail

  @property
  def name(self):
    """
    Get city object name
    :return: str
    """
    return self._name

  @property
  def type(self) -> str:
    """
    Get city object type
    :return: str
    """
    return self._type

  @property
  def volume(self) -> float:
    """
    Get city object volume in cubic meters
    :return: float
    """
    if self._volume is None:
      self._volume = self.simplified_polyhedron.volume
    return self._volume

  @volume.setter
  def volume(self, value):
    """
    Set city object volume in cubic meters
    :param value: float
    """
    self._volume = value

  @property
  def detailed_polyhedron(self) -> Polyhedron:
    """
    Get city object polyhedron including details such as holes
    :return: Polyhedron
    """
    if self._detailed_polyhedron is None:
      polygons = []
      for surface in self.surfaces:
        polygons.append(surface.solid_polygon)
        if surface.holes_polygons is not None:
          for hole_polygon in surface.holes_polygons:
            polygons.append(hole_polygon)
      self._detailed_polyhedron = Polyhedron(polygons)
    return self._detailed_polyhedron

  @property
  def simplified_polyhedron(self) -> Polyhedron:
    """
    Get city object polyhedron, just the simple lod2 representation
    :return: Polyhedron
    """
    if self._simplified_polyhedron is None:
      polygons = []
      for surface in self.surfaces:
        polygons.append(surface.perimeter_polygon)
      self._simplified_polyhedron = Polyhedron(polygons)
    return self._simplified_polyhedron

  @property
  def surfaces(self) -> List[Surface]:
    """
    Get city object surfaces
    :return: [Surface]
    """
    return self._surfaces

  @surfaces.setter
  def surfaces(self, value):
    """
    Set city object surfaces
    :return: [Surface]
    """
    self._surfaces = value

  def surface(self, name) -> Union[Surface, None]:
    """
    Get the city object surface with a given name
    :param name: str
    :return: None or Surface
    """
    for s in self.surfaces:
      if s.name == name:
        return s
    return None

  def surface_by_id(self, identification_number) -> Union[Surface, None]:
    """
    Get the city object surface with a given name
    :param identification_number: str
    :return: None or Surface
    """
    for s in self.surfaces:
      if str(s.id) == str(identification_number):
        return s
    return None

  @property
  def centroid(self) -> List[float]:
    """
    Get city object centroid
    :return: [x,y,z]
    """
    if self._centroid is None:
      self._centroid = self.simplified_polyhedron.centroid
    return self._centroid

  @property
  def max_height(self) -> float:
    """
    Get city object maximal height in meters
    :return: float
    """
    return self.simplified_polyhedron.max_z

  @property
  def external_temperature(self) -> {float}:
    """
    Get external temperature surrounding the city object in Celsius
    :return: dict{dict{[float]}}
    """
    return self._external_temperature

  @external_temperature.setter
  def external_temperature(self, value):
    """
    Set external temperature surrounding the city object in Celsius
    :param value: dict{dict{[float]}}
    """
    self._external_temperature = value

  @property
  def ground_temperature(self) -> dict:
    """
    Get ground temperature under the city object in Celsius at different depths in meters for different time steps
    example of use: {month: {0.5: [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]}}
    :return: dict{dict{[float]}}
    """
    return self._ground_temperature

  @ground_temperature.setter
  def ground_temperature(self, value):
    """
    Set ground temperature under the city object in Celsius at different depths
    :param value: dict{dict{[float]}}
    """
    self._ground_temperature = value

  @property
  def global_horizontal(self) -> dict:
    """
    Get global horizontal radiation surrounding the city object in J/m2
    :return: dict{dict{[float]}}
    """
    return self._global_horizontal

  @global_horizontal.setter
  def global_horizontal(self, value):
    """
    Set global horizontal radiation surrounding the city object in J/m2
    :param value: dict{dict{[float]}}
    """
    self._global_horizontal = value

  @property
  def diffuse(self) -> dict:
    """
    Get diffuse radiation surrounding the city object in J/m2
    :return: dict{dict{[float]}}
    """
    return self._diffuse

  @diffuse.setter
  def diffuse(self, value):
    """
    Set diffuse radiation surrounding the city object in J/m2
    :param value: dict{dict{[float]}}
    """
    self._diffuse = value

  @property
  def direct_normal(self) -> dict:
    """
    Get beam radiation surrounding the city object in J/m2
    :return: dict{dict{[float]}}
    """
    return self._direct_normal

  @direct_normal.setter
  def direct_normal(self, value):
    """
    Set beam radiation surrounding the city object in J/m2
    :param value: dict{dict{[float]}}
    """
    self._direct_normal = value

  @property
  def lower_corner(self):
    """
    Get city object lower corner coordinates [x, y, z]
    :return: [x,y,z]
    """
    if self._city_object_lower_corner is None:
      self._city_object_lower_corner = [self._min_x, self._min_y, self._min_z]
    return self._city_object_lower_corner

  @property
  def upper_corner(self):
    """
    Get city object upper corner coordinates [x, y, z]
    :return: [x,y,z]
    """
    if self._city_object_upper_corner is None:
      self._city_object_upper_corner = [self._max_x, self._max_y, self._max_z]
    return self._city_object_upper_corner

  @property
  def sensors(self) -> List[Sensor]:
    """
    Get sensors belonging to the city object
    :return: [Sensor]
    """
    return self._sensors

  @sensors.setter
  def sensors(self, value):
    """
    Set sensors belonging to the city object
    :param value: [Sensor]
    """
    self._sensors = value

  @property
  def neighbours(self) -> Union[None, List[CityObject]]:
    """
    Get the list of neighbour_objects and their properties associated to the current city_object
    """
    return self._neighbours

  @neighbours.setter
  def neighbours(self, value):
    """
    Set the list of neighbour_objects and their properties associated to the current city_object
    """
    self._neighbours = value

  @property
  def beam(self) -> dict:
    """
    Get beam radiation surrounding the city object in J/m2
    :return: dict{dict{[float]}}
    """
    return self._beam

  @beam.setter
  def beam(self, value):
    """
    Set beam radiation surrounding the city object in J/m2
    :param value: dict{dict{[float]}}
    """
    self._beam = value
