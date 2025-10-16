"""
TestConstructionCatalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Contributors  Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from unittest import TestCase
from hub.catalog_factories.construction_catalog_factory import ConstructionCatalogFactory


class TestConstructionCatalog(TestCase):

  def test_nrel_catalog(self):
    catalog = ConstructionCatalogFactory('nrel').catalog
    catalog_categories = catalog.names()
    constructions = catalog.names('constructions')
    windows = catalog.names('windows')
    materials = catalog.names('materials')
    self.assertEqual(33, len(constructions['constructions']))
    self.assertEqual(5, len(windows['windows']))
    self.assertEqual(33, len(materials['materials']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')

  def test_nrcan_catalog(self):
    catalog = ConstructionCatalogFactory('nrcan').catalog
    catalog_categories = catalog.names()
    constructions = catalog.names('constructions')
    windows = catalog.names('windows')
    materials = catalog.names('materials')
    self.assertEqual(540, len(constructions['constructions']))
    self.assertEqual(96, len(windows['windows']))
    self.assertEqual(552, len(materials['materials']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')

  def test_eilat_catalog(self):
    catalog = ConstructionCatalogFactory('eilat').catalog
    catalog_categories = catalog.names()
    constructions = catalog.names('constructions')
    windows = catalog.names('windows')
    materials = catalog.names('materials')
    self.assertEqual(9, len(constructions['constructions']))
    self.assertEqual(3, len(windows['windows']))
    self.assertEqual(553, len(materials['materials']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')

  def test_palma_catalog(self):
    catalog = ConstructionCatalogFactory('palma').catalog
    catalog_categories = catalog.names()
    constructions = catalog.names('constructions')
    windows = catalog.names('windows')
    materials = catalog.names('materials')
    self.assertEqual(29, len(constructions['constructions']))
    self.assertEqual(9, len(windows['windows']))
    self.assertEqual(122, len(materials['materials']))
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')
