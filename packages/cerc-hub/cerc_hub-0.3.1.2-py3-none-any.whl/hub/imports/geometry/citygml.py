"""
CityGml module parses citygml_classes files and import the geometry into the city model structure
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import logging

import numpy as np
import xmltodict

from hub.city_model_structure.building import Building
from hub.city_model_structure.city import City
from hub.city_model_structure.parts_consisting_building import PartsConsistingBuilding
from hub.helpers.geometry_helper import GeometryHelper
from hub.imports.geometry.citygml_classes.citygml_lod1 import CityGmlLod1
from hub.imports.geometry.citygml_classes.citygml_lod2 import CityGmlLod2


class CityGml:
  """
  CityGml class
  """

  def __init__(self,
               path,
               year_of_construction_field=None,
               function_field=None,
               function_to_hub=None,
               hub_crs=None):
    self._city = None
    self._lod = None
    self._lod1_tags = ['lod1Solid', 'lod1MultiSurface']
    self._lod2_tags = ['lod2Solid', 'lod2MultiSurface', 'lod2MultiCurve']
    self._function_to_hub = function_to_hub
    if hub_crs is None:
      hub_crs = 'EPSG:26911'
    if function_field is None:
      function_field = 'function'
    if year_of_construction_field is None:
      year_of_construction_field = 'yearOfConstruction'
    self._year_of_construction_field = year_of_construction_field
    self._function_field = function_field

    self._lower_corner = None
    self._upper_corner = None
    with open(path, 'r', encoding='utf8') as gml:
      # Clean the namespaces is an important task to prevent wrong ns:field due poor citygml_classes implementations
      force_list = ('cityObjectMember', 'curveMember', 'boundedBy', 'surfaceMember', 'consistsOfBuildingPart')
      self._gml = xmltodict.parse(gml.read(), process_namespaces=True, xml_attribs=True, namespaces={
        'http://www.opengis.net/gml': None,
        'http://www.opengis.net/citygml/1.0': None,
        'http://www.opengis.net/citygml/building/1.0': None,
        'http://schemas.opengis.net/citygml/building/1.0/building.xsd': None,
        'http://www.opengis.net/citygml/appearance/1.0': None,
        'http://schemas.opengis.net/citygml/appearance/1.0/appearance.xsd': None,
        'http://www.opengis.net/citygml/relief/1.0': None,
        'http://schemas.opengis.net/citygml/relief/1.0/relief.xsd': None,
        'http://www.opengis.net/citygml/generics/1.0': None,
        'http://www.w3.org/2001/XMLSchema-instance': None,
        'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0': None,
        'http://www.w3.org/1999/xlink': None,
        'http://www.opengis.net/citygml/relief/2.0': None,
        'http://www.opengis.net/citygml/building/2.0': None,
        'http://www.opengis.net/citygml/building/2.0 http://schemas.opengis.net/citygml/building/2.0/building.xsd '
        'http://www.opengis.net/citygml/relief/2.0 http://schemas.opengis.net/citygml/relief/2.0/relief.xsd" '
        'xmlns="http://www.opengis.net/citygml/2.0': None,
        'http://www.opengis.net/citygml/2.0': None
      }, force_list=force_list)

      self._city_objects = None
      if 'boundedBy' in self._gml['CityModel']:
        for bound in self._gml['CityModel']['boundedBy']:
          envelope = bound['Envelope']
          if '#text' in envelope['lowerCorner']:
            self._lower_corner = np.fromstring(envelope['lowerCorner']['#text'], dtype=float, sep=' ')
            self._upper_corner = np.fromstring(envelope['upperCorner']['#text'], dtype=float, sep=' ')
          else:
            self._lower_corner = np.fromstring(envelope['lowerCorner'], dtype=float, sep=' ')
            self._upper_corner = np.fromstring(envelope['upperCorner'], dtype=float, sep=' ')
          if '@srsName' in envelope:
            self._srs_name = envelope['@srsName']
          else:
            # If not coordinate system given assuming hub standard
            logging.warning(f'gml file contains no coordinate system assuming {hub_crs}')
            self._srs_name = hub_crs
      else:
        # get the boundary from the city objects instead
        for city_object_member in self._gml['CityModel']['cityObjectMember']:
          city_object = city_object_member['Building']
          if 'boundedBy' in city_object:
            for bound in city_object['boundedBy']:
              if 'Envelope' not in bound:
                continue
              envelope = bound['Envelope']
              self._srs_name = envelope['@srsName']
              if '#text' in envelope['lowerCorner']:
                lower_corner = np.fromstring(envelope['lowerCorner']['#text'], dtype=float, sep=' ')
                upper_corner = np.fromstring(envelope['upperCorner']['#text'], dtype=float, sep=' ')
              else:
                lower_corner = np.fromstring(envelope['lowerCorner'], dtype=float, sep=' ')
                upper_corner = np.fromstring(envelope['upperCorner'], dtype=float, sep=' ')
              if self._lower_corner is None:
                self._lower_corner = lower_corner
                self._upper_corner = upper_corner
              else:
                self._lower_corner[0] = min(self._lower_corner[0], lower_corner[0])
                self._lower_corner[1] = min(self._lower_corner[1], lower_corner[1])
                self._lower_corner[2] = min(self._lower_corner[2], lower_corner[2])
                self._upper_corner[0] = max(self._upper_corner[0], upper_corner[0])
                self._upper_corner[1] = max(self._upper_corner[1], upper_corner[1])
                self._upper_corner[2] = max(self._upper_corner[2], upper_corner[2])

  @property
  def content(self):
    """
    Get cityGml raw content
    :return: str
    """
    return self._gml

  def _create_building(self, city_object):
    name = city_object['@id']
    function = None
    year_of_construction = None
    if self._year_of_construction_field in city_object:
      year_of_construction = city_object[self._year_of_construction_field]
    if self._function_field in city_object:
      function = city_object[self._function_field]
      if not isinstance(function, str):
        function = function['#text']
      if self._function_to_hub is not None:
        # use the transformation dictionary to retrieve the proper function
        function = self._function_to_hub[function]

    if any(key in city_object for key in self._lod1_tags):
      if self._lod is None or self._lod > 1:
        self._lod = 1
      surfaces = CityGmlLod1(city_object).surfaces
    elif any(key in city_object for key in self._lod2_tags):
      if self._lod is None or self._lod > 2:
        self._lod = 2
      surfaces = CityGmlLod2(city_object).surfaces
    else:
      raise NotImplementedError("Not supported level of detail")
    return Building(name, surfaces, year_of_construction, function, terrains=None)

  def _create_parts_consisting_building(self, city_object):
    name = city_object['@id']
    building_parts = []
    for part in city_object['consistsOfBuildingPart']:
      building = self._create_building(part['BuildingPart'])
      self._city.add_city_object(building)
      building_parts.append(building)
    return PartsConsistingBuilding(name, building_parts)

  @property
  def city(self) -> City:
    """
    Get city model structure enriched with the geometry information
    :return: City
    """

    if self._city is None:
      self._city = City(self._lower_corner, self._upper_corner, self._srs_name)
      for city_object_member in self._gml['CityModel']['cityObjectMember']:
        city_object = city_object_member['Building']
        if 'consistsOfBuildingPart' in city_object:
          self._city.add_city_objects_cluster(self._create_parts_consisting_building(city_object))
        else:
          self._city.add_city_object(self._create_building(city_object))
      self._city.level_of_detail.geometry = self._lod
      for building in self._city.buildings:
        building.level_of_detail.geometry = self._lod
      lines_information = GeometryHelper.city_mapping(self._city, plot=False)
    return self._city
