"""
Usage catalog factory, publish the usage information
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from pathlib import Path
from typing import TypeVar

from hub.catalog_factories.usage.comnet_catalog import ComnetCatalog
from hub.catalog_factories.usage.nrcan_catalog import NrcanCatalog
from hub.catalog_factories.usage.eilat_catalog import EilatCatalog
from hub.catalog_factories.usage.palma_catalog import PalmaCatalog
from hub.helpers.utils import validate_import_export_type

Catalog = TypeVar('Catalog')


class UsageCatalogFactory:
  """
  Usage catalog factory class
  """
  def __init__(self, handler, base_path=None):
    if base_path is None:
      base_path = Path(Path(__file__).parent.parent / 'data/usage')
    self._catalog_type = '_' + handler.lower()
    validate_import_export_type(UsageCatalogFactory, handler)
    self._path = base_path

  @property
  def _comnet(self):
    """
    Retrieve Comnet catalog
    """
    return ComnetCatalog(self._path)

  @property
  def _nrcan(self):
    """
    Retrieve NRCAN catalog
    """
    # nrcan retrieves the data directly from github
    return NrcanCatalog(self._path)

  @property
  def _palma(self):
    """
    Retrieve Palma catalog
    """
    return PalmaCatalog(self._path)

  @property
  def _eilat(self):
    """
    Retrieve Eilat catalog
    """
    return EilatCatalog(self._path)

  @property
  def catalog(self) -> Catalog:
    """
    Enrich the city given to the class using the class given handler
    :return: Catalog
    """
    return getattr(self, self._catalog_type, lambda: None)
