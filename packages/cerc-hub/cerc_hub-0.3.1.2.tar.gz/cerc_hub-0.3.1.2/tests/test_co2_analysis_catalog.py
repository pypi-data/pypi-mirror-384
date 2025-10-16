'''
TestCo2AnalysisCatalog tests the CO2 Analysis Catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Koa Wells kekoa.wells@concordia.ca
'''

from unittest import TestCase

from hub.catalog_factories.co2_analysis_catalog_factory import Co2AnalysisCatalogFactory


class TestCo2AnalysisCatalog(TestCase):
  '''
  TestCo2AnalysisCatalog TestCase
  '''
  def test_hub_catalog(self):
    catalog = Co2AnalysisCatalogFactory('ecoinvent').catalog
    catalog_categories = catalog.names()
    embodied_co2_windows = catalog.names('embodied_co2_windows')
    end_of_life_co2_windows = catalog.names('end_of_life_co2_windows')
    embodied_co2_materials = catalog.names('embodied_co2_materials')
    end_of_life_co2_materials = catalog.names('end_of_life_co2_materials')

    self.assertEqual(6, len(embodied_co2_windows['embodied_co2_windows']),
                     'Incorrect number of windows in embodied window category')
    self.assertEqual(6, len(end_of_life_co2_windows['end_of_life_co2_windows']),
                     'Incorrect number of windows in end-of-life window category')
    self.assertEqual(12, len(embodied_co2_materials['embodied_co2_materials']),
                     'Incorrect number of materials in embodied material category')
    self.assertEqual(12, len(end_of_life_co2_materials['end_of_life_co2_materials']),
                     'Incorrect number of materials in end-of-life material category')
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')
