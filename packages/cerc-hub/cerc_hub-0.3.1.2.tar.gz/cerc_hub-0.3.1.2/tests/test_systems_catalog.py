"""
TestSystemsCatalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from unittest import TestCase
from hub.catalog_factories.energy_systems_catalog_factory import EnergySystemsCatalogFactory


class TestSystemsCatalog(TestCase):

  def test_montreal_custom_catalog(self):
    catalog = EnergySystemsCatalogFactory('montreal_custom').catalog

    catalog_categories = catalog.names()
    archetypes = catalog.names('archetypes')
    self.assertEqual(23, len(archetypes['archetypes']))
    systems = catalog.names('systems')
    self.assertEqual(18, len(systems['systems']))
    generation_equipments = catalog.names('generation_equipments')
    self.assertEqual(7, len(generation_equipments['generation_equipments']))
    distribution_equipments = catalog.names('distribution_equipments')
    self.assertEqual(13, len(distribution_equipments['distribution_equipments']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')

  def test_montreal_future_catalog(self):
    catalog = EnergySystemsCatalogFactory('montreal_future').catalog

    catalog_categories = catalog.names()
    archetypes = catalog.names()
    self.assertEqual(34, len(archetypes['archetypes']))
    systems = catalog.names('systems')
    self.assertEqual(39, len(systems['systems']))
    generation_equipments = catalog.names('generation_equipments')
    self.assertEqual(49, len(generation_equipments['generation_equipments']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')


  def test_palma_catalog(self):
    catalog = EnergySystemsCatalogFactory('palma').catalog
    catalog_categories = catalog.names()
    archetypes = catalog.names()
    self.assertEqual(15, len(archetypes['archetypes']))
    systems = catalog.names('systems')
    self.assertEqual(13, len(systems['systems']))
    generation_equipments = catalog.names('generation_equipments')
    self.assertEqual(16, len(generation_equipments['generation_equipments']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')
