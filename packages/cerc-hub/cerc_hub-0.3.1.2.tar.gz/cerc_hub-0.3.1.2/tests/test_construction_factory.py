"""
TestConstructionFactory test and validate the city model structure construction parameters
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from pathlib import Path
from unittest import TestCase

from hub.imports.geometry_factory import GeometryFactory
from hub.imports.construction_factory import ConstructionFactory
from hub.helpers.dictionaries import Dictionaries


class TestConstructionFactory(TestCase):
  """
  TestConstructionFactory TestCase
  """
  def setUp(self) -> None:
    """
    Configure test environment
    :return:
    """
    self._city = None
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()

  def _get_citygml(self, file):
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory('citygml', path=file_path).city
    self.assertIsNotNone(self._city, 'city is none')
    self.assertIsNotNone(self._city.level_of_detail.geometry, 'wrong construction level of detail')
    return self._city

  @staticmethod
  def _internal_function(function_format, original_function):
    if function_format == 'hft':
      new_function = Dictionaries().hft_function_to_hub_function[original_function]
    elif function_format == 'pluto':
      new_function = Dictionaries().pluto_function_to_hub_function[original_function]
    else:
      raise Exception('Function key not recognized. Implemented only "hft" and "pluto"')
    return new_function

  def test_citygml_function(self):
    """
    Test city objects' functions in the city
    """
    # case 1: hft
    file = 'one_building_in_kelowna.gml'
    function_format = 'hft'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.function = self._internal_function(function_format, building.function)
      self.assertEqual('residential', building.function, 'format hft')

    # case 2: Pluto
    file = 'pluto_building.gml'
    function_format = 'pluto'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.function = self._internal_function(function_format, building.function)
      self.assertEqual('education', building.function, 'format pluto')

    # case 3: Alkis
    file = 'one_building_in_kelowna_alkis.gml'
    function_format = 'alkis'
    city = self._get_citygml(file)
    for building in city.buildings:
      self.assertRaises(Exception, lambda: self._internal_function(function_format, building.function))

  def _check_buildings(self, city):
    for building in city.buildings:
      self.assertIsNotNone(building.name, 'building name is none')
      self.assertIsNotNone(building.type, 'building type is none')
      self.assertIsNotNone(building.volume, 'building volume is none')
      self.assertIsNotNone(building.detailed_polyhedron, 'building detailed polyhedron is none')
      self.assertIsNotNone(building.simplified_polyhedron, 'building simplified polyhedron is none')
      self.assertIsNotNone(building.surfaces, 'building surfaces is none')
      self.assertIsNotNone(building.centroid, 'building centroid is none')
      self.assertIsNotNone(building.max_height, 'building max_height is none')
      self.assertEqual(len(building.external_temperature), 0, 'building external temperature is calculated')
      self.assertEqual(len(building.global_horizontal), 0, 'building global horizontal is calculated')
      self.assertEqual(len(building.diffuse), 0, 'building diffuse is calculated')
      self.assertEqual(len(building.beam), 0, 'building beam is calculated')
      self.assertIsNotNone(building.lower_corner, 'building lower corner is none')
      self.assertEqual(len(building.sensors), 0, 'building sensors are assigned')
      self.assertIsNotNone(building.internal_zones, 'no internal zones created')
      self.assertIsNotNone(building.grounds, 'building grounds is none')
      self.assertIsNotNone(building.walls, 'building walls is none')
      self.assertIsNotNone(building.roofs, 'building roofs is none')
      self.assertIsNotNone(building.internal_walls, 'building internal walls is none')
      self.assertIsNone(building.basement_heated, 'building basement_heated is not none')
      self.assertIsNone(building.attic_heated, 'building attic_heated is not none')
      self.assertIsNone(building.terrains, 'building terrains is not none')
      self.assertIsNotNone(building.year_of_construction, 'building year_of_construction is none')
      self.assertIsNotNone(building.function, 'building function is none')
      self.assertIsNotNone(building.average_storey_height, 'building average_storey_height is none')
      self.assertIsNotNone(building.storeys_above_ground, 'building storeys_above_ground is none')
      self.assertEqual(len(building.heating_demand), 0, 'building heating is not none')
      self.assertEqual(len(building.cooling_demand), 0, 'building cooling is not none')
      self.assertIsNotNone(building.eave_height, 'building eave height is none')
      self.assertIsNotNone(building.roof_type, 'building roof type is none')
      self.assertIsNotNone(building.floor_area, 'building floor_area is none')
      self.assertIsNone(building.households, 'building households is not none')
      self.assertFalse(building.is_conditioned, 'building is conditioned')
      self.assertIsNotNone(building.shell, 'building shell is none')

  def _check_thermal_zones(self, internal_zone):
    for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
      self.assertIsNotNone(thermal_zone.id, 'thermal_zone id is none')
      self.assertIsNotNone(thermal_zone.footprint_area, 'thermal_zone floor area is none')
      self.assertTrue(len(thermal_zone.thermal_boundaries) > 0, 'thermal_zone thermal_boundaries not defined')
      self.assertIsNotNone(thermal_zone.additional_thermal_bridge_u_value, 'additional_thermal_bridge_u_value is none')
      self.assertIsNotNone(thermal_zone.effective_thermal_capacity, 'thermal_zone effective_thermal_capacity is none')
      self.assertIsNotNone(thermal_zone.infiltration_rate_system_off,
                           'thermal_zone infiltration_rate_system_off is none')
      self.assertIsNotNone(thermal_zone.infiltration_rate_system_on, 'thermal_zone infiltration_rate_system_on is none')
      self.assertIsNotNone(thermal_zone.volume, 'thermal_zone volume is none')
      self.assertIsNone(thermal_zone.ordinate_number, 'thermal_zone ordinate number is not none')
      self.assertIsNotNone(thermal_zone.view_factors_matrix, 'thermal_zone view factors matrix is none')
      self.assertIsNotNone(thermal_zone.total_floor_area, 'thermal zone total_floor_area is none')
      self.assertIsNone(thermal_zone.usage_name, 'thermal_zone usage is not none')
      self.assertIsNone(thermal_zone.hours_day, 'thermal_zone hours a day is not none')
      self.assertIsNone(thermal_zone.days_year, 'thermal_zone days a year is not none')
      self.assertIsNone(thermal_zone.mechanical_air_change, 'thermal_zone mechanical air change is not none')
      self.assertIsNone(thermal_zone.occupancy, 'thermal_zone occupancy is not none')
      self.assertIsNone(thermal_zone.lighting, 'thermal_zone lighting is not none')
      self.assertIsNone(thermal_zone.appliances, 'thermal_zone appliances is not none')
      self.assertIsNone(thermal_zone.thermal_control, 'thermal_zone thermal control is not none')
      self.assertIsNone(thermal_zone.internal_gains, 'thermal_zone internal gains not returns none')

  def _check_thermal_boundaries(self, thermal_zone):
      for thermal_boundary in thermal_zone.thermal_boundaries:
        self.assertIsNotNone(thermal_boundary.id, 'thermal_boundary id is none')
        self.assertIsNotNone(thermal_boundary.parent_surface, 'thermal_boundary surface is none')
        self.assertIsNotNone(thermal_boundary.thermal_zones, 'thermal_boundary delimits no thermal zone')
        self.assertIsNotNone(thermal_boundary.opaque_area, 'thermal_boundary area is none')
        self.assertIsNotNone(thermal_boundary.thickness, 'thermal_boundary thickness is none')
        self.assertIsNotNone(thermal_boundary.type, 'thermal_boundary type is none')
        self.assertIsNotNone(thermal_boundary.thermal_openings, 'thermal_openings is none')
        self.assertIsNotNone(thermal_boundary.window_ratio, 'window_ratio is none')
        self.assertIsNone(thermal_boundary.windows_areas, 'windows_areas is not none')
        self.assertIsNotNone(thermal_boundary.u_value, 'u_value is none')
        self.assertIsNotNone(thermal_boundary.hi, 'hi is none')
        self.assertIsNotNone(thermal_boundary.he, 'he is none')
        self.assertIsNotNone(thermal_boundary.internal_surface, 'virtual_internal_surface is none')
        self.assertIsNotNone(thermal_boundary.layers, 'layers is not none')

  def _check_thermal_openings(self, thermal_boundary):
    for thermal_opening in thermal_boundary.thermal_openings:
      self.assertIsNotNone(thermal_opening.id, 'thermal opening id is not none')
      self.assertIsNotNone(thermal_opening.area, 'thermal opening area is not none')
      self.assertIsNotNone(thermal_opening.frame_ratio, 'thermal opening frame_ratio is none')
      self.assertIsNotNone(thermal_opening.g_value, 'thermal opening g_value is none')
      self.assertIsNotNone(thermal_opening.overall_u_value, 'thermal opening overall_u_value is none')
      self.assertIsNotNone(thermal_opening.hi, 'thermal opening hi is none')
      self.assertIsNotNone(thermal_opening.he, 'thermal opening he is none')

  def _check_surfaces(self, thermal_boundary):
    external_surface = thermal_boundary.external_surface
    internal_surface = thermal_boundary.internal_surface
    self.assertIsNotNone(external_surface.short_wave_reflectance,
                         'external surface short_wave_reflectance id is not none')
    self.assertIsNotNone(external_surface.long_wave_emittance, 'external surface long_wave_emittance id is not none')
    self.assertIsNotNone(internal_surface.short_wave_reflectance,
                         'external surface short_wave_reflectance id is not none')
    self.assertIsNotNone(internal_surface.long_wave_emittance, 'external surface long_wave_emittance id is not none')

  def test_city_with_construction_extended_library(self):
    """
    Enrich the city with the construction information and verify it
    """
    file = 'one_building_in_kelowna.gml'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.year_of_construction = 1980
      building.function = self._internal_function('hft', building.function)
    ConstructionFactory('nrcan', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

    file = 'pluto_building.gml'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.year_of_construction = 1980
      building.function = self._internal_function('pluto', building.function)
    ConstructionFactory('nrcan', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

    file = 'pluto_building.gml'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.year_of_construction = 2006
      building.function = self._internal_function('pluto', building.function)
    ConstructionFactory('nrel', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

    file = 'one_building_in_kelowna.gml'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.year_of_construction = 1980
      building.function = self._internal_function('hft', building.function)
    ConstructionFactory('nrcan', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

    file_path = (self._example_path / 'test.geojson').resolve()
    self._city = GeometryFactory('geojson',
                                 path=file_path,
                                 height_field='citygml_me',
                                 year_of_construction_field='ANNEE_CONS',
                                 function_field='CODE_UTILI',
                                 function_to_hub=Dictionaries().montreal_function_to_hub_function).city

    ConstructionFactory('nrcan', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

  def test_nrcan_construction_factory(self):
    file = 'test.geojson'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='citygml_me',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    ConstructionFactory('nrcan', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

  def test_eilat_construction_factory(self):
    file = 'eilat.geojson'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='heightmax',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           function_to_hub=Dictionaries().eilat_function_to_hub_function).city
    ConstructionFactory('eilat', city).enrich()

    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)

  def test_palma_construction_factory(self):
    file = 'palma_test_file.geojson'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory(file_type='geojson',
                           path=file_path,
                           height_field='measuredHeight',
                           year_of_construction_field='yearOfConstruction',
                           function_field='usage',
                           function_to_hub=Dictionaries().palma_function_to_hub_function).city
    ConstructionFactory('palma', city).enrich()
    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self._check_thermal_zones(internal_zone)
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_boundaries(thermal_zone)
          for thermal_boundary in thermal_zone.thermal_boundaries:
            self.assertIsNotNone(thermal_boundary.layers, 'layers is none')
            self._check_thermal_openings(thermal_boundary)
            self._check_surfaces(thermal_boundary)