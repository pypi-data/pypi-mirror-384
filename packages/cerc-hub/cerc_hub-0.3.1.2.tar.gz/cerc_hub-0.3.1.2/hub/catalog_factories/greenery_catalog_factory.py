"""
Greenery catalog publish the greenery information
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from pathlib import Path
from typing import TypeVar

from hub.catalog_factories.greenery.greenery_catalog import GreeneryCatalog

Catalog = TypeVar('Catalog')


class GreeneryCatalogFactory:
  """
  GreeneryCatalogFactory class
  """
  def __init__(self, handler, base_path=None):
    if base_path is None:
      base_path = (Path(__file__).parent.parent / 'data/greenery').resolve()
    self._handler = '_' + handler.lower()
    self._path = base_path

  @property
  def _nrel(self):
    """
    Return a greenery catalog based in NREL using ecore as datasource
    :return: GreeneryCatalog
    """
    return GreeneryCatalog((self._path / 'ecore_greenery_catalog.xml').resolve())

  @property
  def catalog(self) -> Catalog:
    """
    Enrich the city given to the class using the class given handler
    :return: Catalog
    """
    return getattr(self, self._handler, lambda: None)
