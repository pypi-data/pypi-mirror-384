"""
export a city into Cesium tileset format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import json
import math

import pyproj
from pyproj import Transformer

from hub.helpers.geometry_helper import GeometryHelper


class CesiumjsTileset:
  def __init__(self, city, file_name, target_buildings=None, base_uri=None):
    self._city = city
    self._file_name = file_name
    self._target_buildings = target_buildings
    if base_uri is None:
      base_uri = '.'
    self._base_uri = base_uri
    try:
      srs_name = self._city.srs_name
      if self._city.srs_name in GeometryHelper.srs_transformations:
        srs_name = GeometryHelper.srs_transformations[self._city.srs_name]
      input_reference = pyproj.CRS(srs_name)  # Projected coordinate system from input data
    except pyproj.exceptions.CRSError as err:
      raise pyproj.exceptions.CRSError from err
    self._to_gps = Transformer.from_crs(input_reference, pyproj.CRS('EPSG:4326'))
    city_upper_corner = [
      self._city.upper_corner[0] - self._city.lower_corner[0],
      self._city.upper_corner[1] - self._city.lower_corner[1],
      self._city.upper_corner[2] - self._city.lower_corner[2]
    ]
    city_lower_corner = [0, 0, 0]
    self._tile_set = {
      'asset': {
        'version': '1.1',
        "tilesetVersion": "1.2.3"
      },
      'position': self._to_gps.transform(self._city.lower_corner[0], self._city.lower_corner[1]),
      'schema': {
        'id': "building",
        'classes': {
          'building': {
            "properties": {
              'name': {
                'type': 'STRING'
              },
              'position': {
                'type': 'SCALAR',
                'array': True,
                'componentType': 'FLOAT32'
              },
              'aliases': {
                'type': 'STRING',
                'array': True,
              },
              'volume': {
                'type': 'SCALAR',
                'componentType': 'FLOAT32'
              },
              'floor_area': {
                'type': 'SCALAR',
                'componentType': 'FLOAT32'
              },
              'max_height': {
                'type': 'SCALAR',
                'componentType': 'INT32'
              },
              'year_of_construction': {
                'type': 'SCALAR',
                'componentType': 'INT32'
              },
              'function': {
                'type': 'STRING'
              },
              'usages': {
                'type': 'LIST'
              }
            }
          }
        }
      },
      'geometricError': 500,
      'root': {
        'boundingVolume': {
          'box': CesiumjsTileset._box_values(city_upper_corner, city_lower_corner)
        },
        'geometricError': 70,
        'refine': 'ADD',
        'children': []
      }
    }

    self._export()

  @staticmethod
  def _box_values(upper_corner, lower_corner):

    x = (upper_corner[0] - lower_corner[0]) / 2
    x_center = ((upper_corner[0] - lower_corner[0]) / 2) + lower_corner[0]
    y = (upper_corner[1] - lower_corner[1]) / 2
    y_center = ((upper_corner[1] - lower_corner[1]) / 2) + lower_corner[1]
    z = (upper_corner[2] - lower_corner[2]) / 2
    return [x_center, y_center, z, x, 0, 0, 0, y, 0, 0, 0, z]

  def _ground_coordinates(self, coordinates):
    ground_coordinates = []
    for coordinate in coordinates:
      ground_coordinates.append(
        (coordinate[0] - self._city.lower_corner[0], coordinate[1] - self._city.lower_corner[1])
      )
    return ground_coordinates

  def _export(self):
    for building in self._city.buildings:
      upper_corner = [-math.inf, -math.inf, 0]
      lower_corner = [math.inf, math.inf, 0]
      lower_corner_coordinates = lower_corner
      for surface in building.grounds:  # todo: maybe we should add the terrain?
        coordinates = self._ground_coordinates(surface.solid_polygon.coordinates)
        lower_corner = [min([c[0] for c in coordinates]), min([c[1] for c in coordinates]), 0]
        lower_corner_coordinates = [
          min([c[0] for c in surface.solid_polygon.coordinates]),
          min([c[1] for c in surface.solid_polygon.coordinates]),
          0
        ]
        upper_corner = [max([c[0] for c in coordinates]), max([c[1] for c in coordinates]), building.max_height]

      tile = {
        'boundingVolume': {
          'box': CesiumjsTileset._box_values(upper_corner, lower_corner)
        },
        'geometricError': 250,
        'metadata': {
          'class': 'building',
          'properties': {
            'name': building.name,
            'position': self._to_gps.transform(lower_corner_coordinates[0], lower_corner_coordinates[1]),
            'aliases': building.aliases,
            'volume': building.volume,
            'floor_area': building.floor_area,
            'max_height': building.max_height,
            'year_of_construction': building.year_of_construction,
            'function': building.function,
            'usages': building.usages
          }
        },
        'content': {
          'uri': f'{self._base_uri}/{building.name}.glb'
        }
      }
      self._tile_set['root']['children'].append(tile)

    with open(self._file_name, 'w') as f:
      json.dump(self._tile_set, f, indent=2)
