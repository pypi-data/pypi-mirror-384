"""
Geojson module parses geojson files and import the geometry into the city model structure
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guillermo Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""
import json
import uuid

from pyproj import Transformer

from hub.city_model_structure.city import City
from hub.helpers.geometry_helper import GeometryHelper
from hub.imports.geometry.geojson_classes.geojson_lod0 import GeoJsonLOD0
from hub.imports.geometry.geojson_classes.geojson_lod1 import GeoJsonLOD1


class Geojson:
  """
  Geojson class
  """

  def __init__(self,
               path,
               aliases_field=None,
               extrusion_height_field=None,
               year_of_construction_field=None,
               function_field=None,
               usages_field=None,
               storey_height_field=None,
               function_to_hub=None,
               usages_to_hub=None,
               hub_crs=None
               ):
    self._hub_crs = hub_crs
    if hub_crs is None :
      self._hub_crs = 'epsg:26911'
    self._transformer = Transformer.from_crs('epsg:4326', self._hub_crs)

    self._city = None
    self._buildings = []

    self._aliases_field = aliases_field
    self._extrusion_height_field = extrusion_height_field
    self._year_of_construction_field = year_of_construction_field
    self._function_field = function_field
    self._usages_field = usages_field
    self._storey_height_field = storey_height_field
    self._function_to_hub = function_to_hub
    self._usages_to_hub = usages_to_hub
    with open(path, 'r', encoding='utf8') as json_file:
      self._geojson = json.loads(json_file.read())

  @property
  def city(self) -> City:
    """
    Get city out of a Geojson file
    """
    parser = GeoJsonLOD0(self._transformer)
    lod1_parser = GeoJsonLOD1(self._transformer)
    lod = 0
    if self._city is None:
      for feature in self._geojson['features']:
        extrusion_height = None
        storey_height = None
        if self._extrusion_height_field is not None:
          extrusion_height = float(feature['properties'][self._extrusion_height_field])
          parser = lod1_parser
          lod = 1
          if self._storey_height_field is not None:
            storey_height = float(feature['properties'][self._storey_height_field])

        year_of_construction = None
        if self._year_of_construction_field is not None:
          year_of_construction = int(feature['properties'][self._year_of_construction_field])

        function = None
        if self._function_field is not None:
          function = str(feature['properties'][self._function_field])
          if self._function_to_hub is not None:
            if function in self._function_to_hub:
              function = self._function_to_hub[function]

        usages = None
        if self._usages_field is not None:
          if self._usages_field in feature['properties']:
            usages = feature['properties'][self._usages_field]
            if self._usages_to_hub is not None:
              usages = self._usages_to_hub(usages)

        geometry = feature['geometry']

        if 'id' in feature:
          building_name = feature['id']
        elif 'id' in feature['properties']:
          building_name = feature['properties']['id']
        else:
          building_name = uuid.uuid4()

        building_aliases = []
        if self._aliases_field is not None:
          for alias_field in self._aliases_field:
            building_aliases.append(feature['properties'][alias_field])

        if lod == 0:
          self._buildings.append(parser.parse(
            geometry,
            building_name,
            building_aliases,
            function,
            usages,
            year_of_construction))
        else:
          self._buildings.append(
            parser.parse(
              geometry,
              building_name,
              building_aliases,
              function,
              usages,
              year_of_construction,
              extrusion_height,
              storey_height))
    self._city = parser.city(self._hub_crs)
    for building in self._buildings:
      # Do not include "small building-like structures" to buildings
      storey_height_value = building.storeys_above_ground
      if storey_height_value is None:
        storey_height_value = 1
      if (building.floor_area / storey_height_value) >= 25:
        self._city.add_city_object(building)
    self._city.level_of_detail.geometry = lod
    for building in self._city.buildings:
      building.level_of_detail.geometry = lod
    if lod == 1:
      lines_information = GeometryHelper.city_mapping(self._city, plot=False)
      parser.store_shared_percentage_to_walls(self._city, lines_information)
    return self._city
