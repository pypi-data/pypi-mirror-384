"""
TestMontrealCustomCatalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Atiya atiya.atiya@mail.concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from unittest import TestCase
from hub.catalog_factories.costs_catalog_factory import CostsCatalogFactory


class TestCostsCatalog(TestCase):

  def test_costs_catalog(self):
    catalog = CostsCatalogFactory('montreal_custom').catalog
    catalog_categories = catalog.names()
    self.assertIsNotNone(catalog, 'catalog is none')
    content = catalog.entries()
    self.assertTrue(len(content.archetypes) == 2)

    # retrieving all the entries should not raise any exceptions
    for category in catalog_categories:
      for value in catalog_categories[category]:
        catalog.get_entry(value)

    with self.assertRaises(IndexError):
      catalog.get_entry('unknown')
