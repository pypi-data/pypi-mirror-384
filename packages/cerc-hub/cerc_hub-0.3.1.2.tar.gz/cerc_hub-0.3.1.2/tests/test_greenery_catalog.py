"""
Test greenery factory test and validate the greenery construction
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from unittest import TestCase

from hub.catalog_factories.greenery_catalog_factory import GreeneryCatalogFactory


class TestGreeneryCatalog(TestCase):
  def test_catalog(self):
    catalog = GreeneryCatalogFactory('nrel').catalog
    catalog_categories = catalog.names()
    vegetations = catalog.names('vegetations')
    plants = catalog.names('plants')
    soils = catalog.names('soils')
    self.assertTrue(len(catalog_categories) == 3)
    self.assertTrue(len(vegetations['vegetations']) == 4)
    self.assertTrue(len(plants['plants']) == 14)
    self.assertTrue(len(soils['soils']) == 6)
    with self.assertRaises(ValueError):
      catalog.names('unknown')

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')

    self.assertTrue(len(catalog.entries().vegetations) == 4)
    self.assertTrue(len(catalog.entries().plants) == 14)
    self.assertTrue(len(catalog.entries().soils) == 6)
