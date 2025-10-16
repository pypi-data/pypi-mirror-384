"""
TestGeometryFactory test and validate the city model structure geometric parameters
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from pathlib import Path
from unittest import TestCase
import hub.exports.exports_factory
from hub.helpers.dictionaries import Dictionaries
from hub.helpers.geometry_helper import GeometryHelper
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.geometry_factory import GeometryFactory


class TestGeometryFactory(TestCase):
  """
  Non-functional TestGeometryFactory
  Load testing
  """

  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._city = None
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()
    self._output_path = (Path(__file__).parent / 'tests_outputs').resolve()

  def _get_city(self, file, file_type, height_field=None, year_of_construction_field=None, function_field=None):
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory(file_type,
                                 path=file_path,
                                 height_field=height_field,
                                 year_of_construction_field=year_of_construction_field,
                                 function_field=function_field,
                                 function_to_hub=Dictionaries().montreal_function_to_hub_function
                                 ).city
    self.assertIsNotNone(self._city, 'city is none')
    return self._city

  def _check_buildings(self, city):
    for building in city.buildings:
      self.assertIsNotNone(building.name, 'building name is none')
      self.assertIsNotNone(building.type, 'building type is none')
      self.assertIsNotNone(building.volume, 'building volume is none')
      self.assertIsNotNone(building.detailed_polyhedron, 'building detailed polyhedron is none')
      self.assertIsNotNone(building.simplified_polyhedron, 'building simplified polyhedron is none')
      self.assertIsNotNone(building.surfaces, 'building surfaces is none')
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
      self.assertIsNotNone(building.internal_zones, 'building internal zones is none')
      for internal_zone in building.internal_zones:
        self.assertIsNone(internal_zone.usages, 'usage zones are defined')
        self.assertIsNone(internal_zone.thermal_archetype, 'thermal archetype is defined')
      self.assertIsNone(building.basement_heated, 'building basement_heated is not none')
      self.assertIsNone(building.attic_heated, 'building attic_heated is not none')
      self.assertIsNone(building.terrains, 'building terrains is not none')
      self.assertIsNone(building.average_storey_height, 'building average_storey_height is not none')
      self.assertIsNone(building.storeys_above_ground, 'building storeys_above_ground is not none')
      self.assertEqual(len(building.heating_demand), 0, 'building heating is not none')
      self.assertEqual(len(building.cooling_demand), 0, 'building cooling is not none')
      self.assertIsNotNone(building.eave_height, 'building eave height is none')
      self.assertIsNotNone(building.roof_type, 'building roof type is none')
      self.assertIsNotNone(building.floor_area, 'building floor_area is none')
      self.assertIsNone(building.households, 'building households is not none')
      self.assertFalse(building.is_conditioned, 'building is_conditioned is conditioned')

  def _check_surfaces(self, building):
    for surface in building.surfaces:
      self.assertIsNotNone(surface.name, 'surface name is none')
      self.assertIsNotNone(surface.id, 'surface id is none')
      self.assertIsNotNone(surface.lower_corner, 'surface envelope_lower_corner is none')
      self.assertIsNotNone(surface.upper_corner, 'surface envelope_upper_corner is none')
      self.assertIsNotNone(surface.perimeter_area, 'surface area_above_ground is none')
      self.assertIsNotNone(surface.azimuth, 'surface azimuth is none')
      self.assertIsNotNone(surface.inclination, 'surface inclination is none')
      self.assertIsNotNone(surface.type, 'surface type is none')
      self.assertEqual(len(surface.global_irradiance), 0, 'global irradiance is calculated')
      self.assertIsNotNone(surface.perimeter_polygon, 'surface perimeter_polygon is none')
      self.assertIsNone(surface.holes_polygons, 'surface hole_polygons is not none')
      self.assertIsNotNone(surface.solid_polygon, 'surface solid_polygon is none')
      self.assertIsNone(surface.short_wave_reflectance, 'surface short_wave_reflectance is not none')
      self.assertIsNone(surface.long_wave_emittance, 'surface long_wave_emittance is not none')
      self.assertIsNotNone(surface.inverse, 'surface inverse is none')
      self.assertIsNone(surface.associated_thermal_boundaries, 'associated_thermal_boundaries are assigned')
      self.assertIsNone(surface.vegetation, 'surface vegetation is not none')

  # citygml_classes
  def test_import_citygml(self):
    """
    Test city objects in the city
    :return: None
    """
    file = 'FZK_Haus_LoD_2.gml'
    city = self._get_city(file, 'citygml')
    self.assertTrue(len(city.buildings) == 1)
    self._check_buildings(city)
    for building in city.buildings:
      self._check_surfaces(building)
      city = ConstructionFactory('nrel', city).enrich()

  def test_import_obj(self):
    """
    Test obj import
    """
    file = 'kelowna.obj'
    city = self._get_city(file, 'obj')
    self.assertTrue(len(city.buildings) == 1)
    self._check_buildings(city)
    for building in city.buildings:
      self._check_surfaces(building)

  def test_import_geojson(self):
    """
    Test geojson import
    """
    file = Path(self._example_path / 'test.geojson').resolve()
    city = GeometryFactory('geojson',
                           path=file,
                           height_field='citygml_me',
                           year_of_construction_field='ANNEE_CONS',
                           aliases_field=['ID_UEV', 'CIVIQUE_DE', 'NOM_RUE'],
                           function_field='CODE_UTILI',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    hub.exports.exports_factory.ExportsFactory('obj', city, self._output_path).export()
    for building in city.building_alias('01002777'):
      self.assertEqual('1', building.name, 'Wrong building name when looking for alias')
    self.assertEqual(8, len(city.building_alias('rue Sherbrooke Ouest  (MTL+MTO+WMT)')))
    self.assertEqual(17, len(city.buildings), 'wrong number of buildings')

    self.assertIsNotNone(city.city_object('15'), 'Building name 15 is missing in the city')
    city.remove_city_object(city.city_object('15'))
    self.assertIsNone(city.city_object('15'), 'Building name 15 wasn\'t removed')
    for building in city.buildings:
      _building = city.city_object(building.name)
      self.assertEqual(_building.name, building.name, 'hash map it\'s unsync')

  def test_map_neighbours(self):
    """
    Test neighbours map creation
    """
    file = 'test.geojson'

    city = self._get_city(file, 'geojson',
                          year_of_construction_field='ANNEE_CONS',
                          function_field='LIBELLE_UT')
    info_lod0 = GeometryHelper.city_mapping(city, plot=False)
    city = self._get_city(file, 'geojson',
                          height_field='citygml_me',
                          year_of_construction_field='ANNEE_CONS',
                          function_field='LIBELLE_UT')
    info_lod1 = GeometryHelper.city_mapping(city, plot=False)
    hub.exports.exports_factory.ExportsFactory('obj', city, self._output_path).export()
    self.assertEqual(info_lod0, info_lod1)
    self.assertEqual(2, len(city.city_object('1').neighbours))
    self.assertEqual(3, len(city.city_object('2').neighbours))
    self.assertEqual(2, len(city.city_object('3').neighbours))
    self.assertEqual(2, len(city.city_object('4').neighbours))
    self.assertEqual(3, len(city.city_object('5').neighbours))
    self.assertEqual(3, len(city.city_object('6').neighbours))
    self.assertEqual(1, len(city.city_object('8').neighbours))
    self.assertEqual(2, len(city.city_object('9').neighbours))
    self.assertEqual(2, len(city.city_object('10').neighbours))
    self.assertEqual(2, len(city.city_object('11').neighbours))
    self.assertEqual(2, len(city.city_object('12').neighbours))
    self.assertEqual(1, len(city.city_object('13').neighbours))
    self.assertEqual(2, len(city.city_object('14').neighbours))
    self.assertEqual(1, len(city.city_object('15').neighbours))
    self.assertEqual(1, len(city.city_object('16').neighbours))
    self.assertEqual(2, len(city.city_object('67').neighbours))
    self.assertEqual(1, len(city.city_object('68').neighbours))

    self.assertEqual('12', city.city_object('8').neighbours[0].name)
    self.assertEqual('14', city.city_object('13').neighbours[0].name)
    self.assertEqual('14', city.city_object('15').neighbours[0].name)
