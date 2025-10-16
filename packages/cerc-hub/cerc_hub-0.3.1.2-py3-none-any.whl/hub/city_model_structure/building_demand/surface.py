"""
Surface module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from __future__ import annotations

import math
import uuid
from typing import List, Union
import numpy as np
from hub.city_model_structure.attributes.polygon import Polygon
from hub.city_model_structure.attributes.plane import Plane
from hub.city_model_structure.attributes.point import Point
from hub.city_model_structure.greenery.vegetation import Vegetation
from hub.city_model_structure.building_demand.thermal_boundary import ThermalBoundary
import hub.helpers.constants as cte
from hub.helpers.configuration_helper import ConfigurationHelper


class Surface:
  """
  Surface class
  """

  def __init__(self, solid_polygon, perimeter_polygon, holes_polygons=None, name=None, surface_type=None):
    self._type = surface_type
    self._name = name
    self._id = None
    self._azimuth = None
    self._inclination = None
    self._area = None
    self._lower_corner = None
    self._upper_corner = None
    self._global_irradiance = {}
    self._perimeter_polygon = perimeter_polygon
    self._holes_polygons = holes_polygons
    self._solid_polygon = solid_polygon
    self._short_wave_reflectance = None
    self._long_wave_emittance = None
    self._inverse = None
    self._associated_thermal_boundaries = None
    self._vegetation = None
    self._percentage_shared = None
    self._solar_collectors_area_reduction_factor = None
    self._global_irradiance_tilted = {}
    self._installed_solar_collector_area = None

  @property
  def name(self):
    """
    Get the surface name
    :return: str
    """
    if self._name is None:
      self._name = str(uuid.uuid4())
    return self._name

  @property
  def id(self):
    """
    Get the surface id
    :return: str
    """
    if self._id is None:
      raise ValueError('Undefined surface id')
    return self._id

  @id.setter
  def id(self, value):
    """
    Set the surface id
    :param value: str
    """
    if value is not None:
      self._id = str(value)

  def _max_coord(self, axis):
    if axis == 'x':
      axis = 0
    elif axis == 'y':
      axis = 1
    else:
      axis = 2
    max_coordinate = ''
    for point in self.perimeter_polygon.coordinates:
      if max_coordinate == '':
        max_coordinate = point[axis]
      elif max_coordinate < point[axis]:
        max_coordinate = point[axis]
    return max_coordinate

  def _min_coord(self, axis):
    if axis == 'x':
      axis = 0
    elif axis == 'y':
      axis = 1
    else:
      axis = 2
    min_coordinate = ''
    for point in self.perimeter_polygon.coordinates:
      if min_coordinate == '':
        min_coordinate = point[axis]
      elif min_coordinate > point[axis]:
        min_coordinate = point[axis]
    return min_coordinate

  @property
  def lower_corner(self):
    """
    Get surface's lower corner [x, y, z]
    :return: [float]
    """
    if self._lower_corner is None:
      self._lower_corner = [self._min_coord('x'), self._min_coord('y'), self._min_coord('z')]
    return self._lower_corner

  @property
  def upper_corner(self):
    """
    Get surface's upper corner [x, y, z]
    :return: [float]
    """
    if self._upper_corner is None:
      self._upper_corner = [self._max_coord('x'), self._max_coord('y'), self._max_coord('z')]
    return self._upper_corner

  @property
  def perimeter_area(self):
    """
    Get perimeter surface area in square meters (opaque + transparent)
    :return: float
    """
    self._area = self.perimeter_polygon.area
    return self._area

  @property
  def azimuth(self):
    """
    Get surface azimuth in radians (north = 0)
    :return: float
    """
    if self._azimuth is None:
      normal = self.perimeter_polygon.normal
      self._azimuth = (np.pi/2) - np.arctan2(normal[1], normal[0])
    return self._azimuth

  @property
  def inclination(self):
    """
    Get surface inclination in radians (zenith = 0, horizon = pi/2)
    :return: float
    """
    if self._inclination is None:
      self._inclination = np.arccos(self.perimeter_polygon.normal[2])
    return self._inclination

  @property
  def type(self):
    """
    Get surface type Ground, Ground wall, Wall, Attic floor, Interior slab, Interior wall, Roof or Virtual internal
    If the geometrical LoD is lower than 4,
    the surfaces' types are not defined in the importer and can only be Ground, Wall or Roof
    :return: str
    """
    if self._type is None:
      inclination_cos = math.cos(self.inclination)
      # 170 degrees
      if inclination_cos <= -0.98:
        self._type = 'Ground'
      # between 80 and 100 degrees
      elif abs(inclination_cos) <= 0.17:
        self._type = 'Wall'
      else:
        self._type = 'Roof'
    return self._type

  @property
  def global_irradiance(self) -> dict:
    """
    Get global irradiance on surface in W/m2
    :return: dict
    """
    return self._global_irradiance

  @global_irradiance.setter
  def global_irradiance(self, value):
    """
    Set global irradiance on surface in W/m2
    :param value: dict
    """
    self._global_irradiance = value

  @property
  def perimeter_polygon(self) -> Polygon:
    """
    Get a polygon surface defined by the perimeter, merging solid and holes
    :return: Polygon
    """
    return self._perimeter_polygon

  @property
  def solid_polygon(self) -> Polygon:
    """
    Get the solid surface
    :return: Polygon
    """
    return self._solid_polygon

  @solid_polygon.setter
  def solid_polygon(self, value):
    """
    Set the solid surface
    :return: Polygon
    """
    self._solid_polygon = value

  @property
  def holes_polygons(self) -> Union[List[Polygon], None]:
    """
    Get hole surfaces, a list of hole polygons found in the surface
    :return: None, [] or [Polygon]
    None -> not known whether holes exist in reality or not due to low level of detail of input data
    [] -> no holes in the surface
    [Polygon] -> one or more holes in the surface
    """
    return self._holes_polygons

  @holes_polygons.setter
  def holes_polygons(self, value):
    """
    Set the hole surfaces
    :param value: [Polygon]
    """
    self._holes_polygons = value

  @property
  def short_wave_reflectance(self):
    """
    Get the short wave reflectance, this includes all solar spectrum, visible and not visible
    The absorptance as an opaque surface, can be calculated as 1-short_wave_reflectance
    :return: float
    """
    return self._short_wave_reflectance

  @short_wave_reflectance.setter
  def short_wave_reflectance(self, value):
    """
    Set the short wave reflectance, this includes all solar spectrum, visible and not visible
    The absorptance as an opaque surface, can be calculated as 1-short_wave_reflectance
    :param value: float
    """
    self._short_wave_reflectance = value

  @property
  def long_wave_emittance(self):
    """
    Get the long wave emittance af the surface
    The thermal absorptance can be calculated as 1-long_wave_emittance
    :return: float
    """
    return self._long_wave_emittance

  @long_wave_emittance.setter
  def long_wave_emittance(self, value):
    """
    Set the long wave emittance af the surface
    The thermal absorptance can be calculated as 1-long_wave_emittance
    :param value: float
    """
    self._long_wave_emittance = value

  @property
  def inverse(self) -> Surface:
    """
    Get the inverse surface (the same surface pointing backwards)
    :return: Surface
    """
    if self._inverse is None:
      new_solid_polygon = Polygon(self.solid_polygon.inverse)
      new_perimeter_polygon = Polygon(self.perimeter_polygon.inverse)
      new_holes_polygons = []
      if self.holes_polygons is not None:
        for hole in self.holes_polygons:
          new_holes_polygons.append(Polygon(hole.inverse))
      else:
        new_holes_polygons = None
      self._inverse = Surface(new_solid_polygon, new_perimeter_polygon, new_holes_polygons, cte.VIRTUAL_INTERNAL)
    return self._inverse

  def divide(self, z):
    """
    Divides a surface at Z plane
    :return: Surface, Surface, Any
    """
    # todo: check return types
    #  recheck this method for LoD3 (windows)
    origin = Point([0, 0, z])
    normal = np.array([0, 0, 1])
    plane = Plane(normal=normal, origin=origin)
    polygon = self.perimeter_polygon
    part_1, part_2, intersection = polygon.divide(plane)
    surface_child = Surface(part_1, part_1, name=self.name, surface_type=self.type)
    rest_surface = Surface(part_2, part_2, name=self.name, surface_type=self.type)
    return surface_child, rest_surface, intersection

  @property
  def vegetation(self) -> Union[None, Vegetation]:
    """
    Get the vegetation construction at the external surface of the thermal boundary
    :return: None or Vegetation
    """
    return self._vegetation

  @vegetation.setter
  def vegetation(self, value):
    """
    Set the vegetation construction at the external surface of the thermal boundary
    :param value: Vegetation
    """
    self._vegetation = value

  @property
  def associated_thermal_boundaries(self) -> Union[None, List[ThermalBoundary]]:
    """
    Get the list of thermal boundaries that has this surface as external face
    :return: None or [ThermalBoundary]
    """
    return self._associated_thermal_boundaries

  @associated_thermal_boundaries.setter
  def associated_thermal_boundaries(self, value):
    """
    Set the list of thermal boundaries that has this surface as external face
    :param value: None or [ThermalBoundary]
    """
    self._associated_thermal_boundaries = value

  @property
  def percentage_shared(self):
    """
    Get percentage of the wall shared with other walls
    :return: float
    """
    return self._percentage_shared

  @percentage_shared.setter
  def percentage_shared(self, value):
    """
    Set percentage of the wall shared with other walls
    :param value: float
    """
    self._percentage_shared = value

  @property
  def solar_collectors_area_reduction_factor(self):
    """
    Get factor area collector per surface area if set or calculate using Romero Rodriguez, L. et al (2017) model if not
    :return: float
    """
    if self._solar_collectors_area_reduction_factor is None:
      if self.type == cte.ROOF:
        _protected_building_restriction = 1
        # 10 degrees range
        if abs(math.sin(self.inclination)) < 0.17:
          # horizontal
          _construction_restriction = 0.8
          _separation_of_panels = 0.46
          _shadow_between_panels = 0.7
        else:
          # tilted
          _construction_restriction = 0.9
          _separation_of_panels = 0.9
          _shadow_between_panels = 1
        self._solar_collectors_area_reduction_factor = (
            _protected_building_restriction * _construction_restriction * _separation_of_panels * _shadow_between_panels
        )
    return self._solar_collectors_area_reduction_factor

  @solar_collectors_area_reduction_factor.setter
  def solar_collectors_area_reduction_factor(self, value):
    """
    Set factor area collector per surface area
    :param value: float
    """
    self._solar_collectors_area_reduction_factor = value

  @property
  def global_irradiance_tilted(self) -> dict:
    """
    Get global irradiance on a tilted surface in W/m2
    :return: dict
    """
    return self._global_irradiance_tilted

  @global_irradiance_tilted.setter
  def global_irradiance_tilted(self, value):
    """
    Set global irradiance on a tilted surface in W/m2
    :param value: dict
    """
    self._global_irradiance_tilted = value

  @property
  def installed_solar_collector_area(self):
    """
    Get installed solar collector area in m2
    :return: dict
    """
    return self._installed_solar_collector_area

  @installed_solar_collector_area.setter
  def installed_solar_collector_area(self, value):
    """
    Set installed solar collector area in m2
    :return: dict
    """
    self._installed_solar_collector_area = value