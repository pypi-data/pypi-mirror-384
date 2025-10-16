"""
ExportsFactory export a city into several formats
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from pathlib import Path

from hub.exports.formats.glb import Glb
from hub.exports.formats.obj import Obj
from hub.exports.formats.geojson import Geojson
from hub.exports.formats.simplified_radiosity_algorithm import SimplifiedRadiosityAlgorithm
from hub.exports.formats.stl import Stl
from hub.exports.formats.cesiumjs_tileset import CesiumjsTileset
from hub.helpers.utils import validate_import_export_type


class ExportsFactory:
  """
  Exports factory class
  """
  def __init__(self, handler, city, path, target_buildings=None, adjacent_buildings=None, base_uri=None):
    self._city = city
    self._handler = '_' + handler.lower()
    validate_import_export_type(ExportsFactory, handler)
    if isinstance(path, str):
      path = Path(path)
    self._path = path
    self._target_buildings = target_buildings
    self._adjacent_buildings = adjacent_buildings
    self._base_uri = base_uri

  def _stl(self):
    """
    Export the city geometry to stl
    :return: None
    """
    return Stl(self._city, self._path)

  def _obj(self):
    """
    Export the city geometry to obj
    :return: None
    """
    return Obj(self._city, self._path)

  def _sra(self):
    """
    Export the city to Simplified Radiosity Algorithm xml format
    :return: None
    """
    return SimplifiedRadiosityAlgorithm(
      self._city, (self._path / f'{self._city.name}_sra.xml'), target_buildings=self._target_buildings
    )

  def _cesiumjs_tileset(self):
    """
    Export the city to a cesiumJs tileset format
    :return: None
    """
    return CesiumjsTileset(
      self._city,
      (self._path / f'{self._city.name}.json'),
      target_buildings=self._target_buildings,
      base_uri=self._base_uri
    )

  def _glb(self):
    return Glb(self._city, self._path, target_buildings=self._target_buildings)

  def _geojson(self):
    return Geojson(self._city, self._path, target_buildings=self._target_buildings).export()

  def export(self):
    """
    Export the city given to the class using the given export type handler
    :return: None
    """
    _handlers = {
      '_stl': self._stl,
      '_obj': self._obj,
      '_sra': self._sra,
      '_cesiumjs_tileset': self._cesiumjs_tileset,
      '_glb': self._glb,
      '_geojson': self._geojson,
    }
    return _handlers[self._handler]()
