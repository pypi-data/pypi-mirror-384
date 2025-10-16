"""
CityGmlLod1 module parses citygml_classes files with level of detail 1 and import the geometry into the city model
structure
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.imports.geometry.citygml_classes.citygml_base import CityGmlBase
from hub.imports.geometry.helpers.geometry_helper import GeometryHelper
from hub.city_model_structure.building_demand.surface import Surface
from hub.city_model_structure.attributes.polygon import Polygon


class CityGmlLod2(CityGmlBase):
  """
  CityGmlLod1 class to parse level of detail 1 city gml files
  """
  def __init__(self, city_object_member):
    super().__init__()
    self._city_object_member = city_object_member
    self._surfaces = self._identify(self._city_object_member)

  @classmethod
  def _identify(cls, city_object_member):
    if 'lod2Solid' in city_object_member:
      return cls._solid(city_object_member)
    if 'lod2MultiSurface' in city_object_member:
      return cls._multi_surface(city_object_member)
    if 'lod2MultiCurve' in city_object_member:
      return cls._multi_curve(city_object_member)
    raise NotImplementedError(city_object_member)

  @staticmethod
  def _surface_encoding(surfaces):
    if 'lod2MultiSurface' in surfaces:
      return 'lod2MultiSurface', 'MultiSurface'
    raise NotImplementedError('unknown surface type')

  @classmethod
  def _solid(cls, city_object_member):
    surfaces = []
    for bounded in city_object_member["boundedBy"]:
      try:
        surface_type = next(iter(bounded))
      except TypeError:
        continue
      try:
        surface_encoding, surface_subtype = cls._surface_encoding(bounded[surface_type])
      except NotImplementedError:
        continue
      if 'surfaceMember' not in bounded[surface_type][surface_encoding][surface_subtype]:
        continue
      for member in bounded[surface_type][surface_encoding][surface_subtype]['surfaceMember']:
        if 'CompositeSurface' in member:
          for composite_members in member['CompositeSurface']['surfaceMember']:
            for composite_member in composite_members['CompositeSurface']['surfaceMember']:
              surfaces.append(cls._add_member_surface(composite_member, surface_type))
        else:
          surfaces.append(cls._add_member_surface(member, surface_type))
    return surfaces

  @classmethod
  def _add_member_surface(cls, member, surface_type):
    pos_name = 'posList'
    if pos_name not in member['Polygon']['exterior']['LinearRing']:
      pos_name = 'pos'
    if '@srsDimension' in member['Polygon']['exterior']['LinearRing'][pos_name]:
      gml_points = member['Polygon']['exterior']['LinearRing']['posList']["#text"]
    else:
      gml_points = member['Polygon']['exterior']['LinearRing'][pos_name]
    if pos_name == 'pos':
      gml_points_string = ''
      for gml_point in gml_points:
        gml_points_string = f'{gml_points_string} {gml_point}'
      gml_points = gml_points_string.lstrip(' ')
    solid_points = GeometryHelper.points_from_string(GeometryHelper.remove_last_point_from_string(gml_points))
    polygon = Polygon(solid_points)
    return Surface(polygon, polygon, surface_type=GeometryHelper.gml_surface_to_hub(surface_type))

  @classmethod
  def _multi_curve(cls, city_object_member):
    raise NotImplementedError('multi curve')

  @classmethod
  def _multi_surface(cls, city_object_member):
    return cls._solid(city_object_member)
