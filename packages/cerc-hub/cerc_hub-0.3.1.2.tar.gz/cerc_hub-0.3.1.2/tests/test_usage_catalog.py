"""
TestUsageCatalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from unittest import TestCase
from hub.catalog_factories.usage_catalog_factory import UsageCatalogFactory


class TestConstructionCatalog(TestCase):
  def test_comnet_catalog(self):
    catalog = UsageCatalogFactory('comnet').catalog
    self.assertIsNotNone(catalog, 'catalog is none')
    content = catalog.entries()
    self.assertEqual(32, len(content.usages), 'Wrong number of usages')

  def test_nrcan_catalog(self):
    catalog = UsageCatalogFactory('nrcan').catalog
    self.assertIsNotNone(catalog, 'catalog is none')
    content = catalog.entries()
    self.assertEqual(34, len(content.usages), 'Wrong number of usages')

  def test_palma_catalog(self):
    catalog = UsageCatalogFactory('palma').catalog
    self.assertIsNotNone(catalog, 'catalog is none')
    content = catalog.entries()
    self.assertEqual(1, len(content.usages), 'Wrong number of usages')
