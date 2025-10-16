"""
CityGmlLod1 module parses citygml_classes files with level of detail 1 and import the geometry into the city model
structure
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.imports.geometry.helpers.geometry_helper import GeometryHelper
from hub.imports.geometry.citygml_classes.citygml_base import CityGmlBase
from hub.city_model_structure.building_demand.surface import Surface
from hub.city_model_structure.attributes.polygon import Polygon


class CityGmlLod1(CityGmlBase):
  """
  CityGmlLod1 class to parse level of detail 1 city gml files
  """

  @classmethod
  def _multi_curve(cls, city_object_member):
    pass

  def __init__(self, city_object_member):
    super().__init__()
    self._city_object_member = city_object_member
    self._surfaces = self._identify(self._city_object_member)

  @classmethod
  def _identify(cls, city_object_member):
    if 'lod1Solid' in city_object_member:
      return cls._solid(city_object_member)
    if 'lod1MultiSurface' in city_object_member:
      return cls._multi_surface(city_object_member)
    raise NotImplementedError(city_object_member)

  @classmethod
  def _solid(cls, city_object_member):
    try:
      solid_points = [
        GeometryHelper.points_from_string(GeometryHelper.remove_last_point_from_string(
          s['Polygon']['exterior']['LinearRing']['posList']['#text']))
        for s in city_object_member['lod1Solid']['Solid']['exterior']['CompositeSurface']['surfaceMember']]
    except TypeError:
      solid_points = [
        GeometryHelper.points_from_string(GeometryHelper.remove_last_point_from_string(
          s['Polygon']['exterior']['LinearRing']['posList']))
        for s in city_object_member['lod1Solid']['Solid']['exterior']['CompositeSurface']['surfaceMember']]

    return [Surface(Polygon(sp), Polygon(sp)) for sp in solid_points]

  @classmethod
  def _multi_surface(cls, city_object_member):
    solid_points = [GeometryHelper.points_from_string(GeometryHelper.remove_last_point_from_string(
      s['Polygon']['exterior']['LinearRing']['posList']))
                    for s in city_object_member['Building']['lod1MultiSurface']['MultiSurface']['surfaceMember']]
    return [Surface(Polygon(sp), Polygon(sp)) for sp in solid_points]
