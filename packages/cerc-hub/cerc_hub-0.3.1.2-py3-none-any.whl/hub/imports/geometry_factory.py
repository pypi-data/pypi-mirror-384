"""
GeometryFactory retrieve the specific geometric module to load the given format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.city_model_structure.city import City
from hub.helpers.utils import validate_import_export_type
from hub.imports.geometry.citygml import CityGml
from hub.imports.geometry.geojson import Geojson
from hub.imports.geometry.obj import Obj


class GeometryFactory:
  """
  GeometryFactory class
  """

  def __init__(self, file_type,
               path=None,
               aliases_field=None,
               height_field=None,
               year_of_construction_field=None,
               function_field=None,
               usages_field=None,
               storey_height_field=None,
               function_to_hub=None,
               usages_to_hub=None,
               hub_crs=None):

    self._file_type = '_' + file_type.lower()
    validate_import_export_type(GeometryFactory, file_type)
    self._path = path
    self._aliases_field = aliases_field
    self._height_field = height_field
    self._year_of_construction_field = year_of_construction_field
    self._function_field = function_field
    self._usages_field = usages_field
    self._storey_height_field = storey_height_field
    self._function_to_hub = function_to_hub
    self._usages_to_hub = usages_to_hub
    self._hub_crs = hub_crs

  def _citygml(self) -> City:
    """
    Enrich the city by using CityGML information as data source
    :return: City
    """
    return CityGml(self._path,
                   self._year_of_construction_field,
                   self._function_field,
                   self._function_to_hub,
                   self._hub_crs).city

  def _obj(self) -> City:
    """
    Enrich the city by using OBJ information as data source
    :return: City
    """
    return Obj(self._path).city

  def _geojson(self) -> City:
    """
    Enrich the city by using Geojson information as data source
    :return: City
    """
    return Geojson(self._path,
                   self._aliases_field,
                   self._height_field,
                   self._year_of_construction_field,
                   self._function_field,
                   self._usages_field,
                   self._storey_height_field,
                   self._function_to_hub,
                   self._usages_to_hub,
                   self._hub_crs).city

  @property
  def city(self) -> City:
    """
    Enrich the city given to the class using the class given handler
    :return: City
    """
    _handlers = {
      '_citygml': self._citygml,
      '_obj': self._obj,
      '_geojson': self._geojson,
    }
    return _handlers[self._file_type]()
