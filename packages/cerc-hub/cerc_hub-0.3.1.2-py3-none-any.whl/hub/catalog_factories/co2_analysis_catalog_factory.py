"""
CO2 analysis catalog factory
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""

from pathlib import Path
from typing import TypeVar

from hub.catalog_factories.co2_analysis._ecoinvent_catalog import EcoinventCatalog
from hub.helpers.utils import validate_import_export_type

Catalog = TypeVar('Catalog')


class Co2AnalysisCatalogFactory:
  """
  Co2AnalysisCatalogFactory class
  """
  def __init__(self, handler, base_path=None):
    if base_path is None:
      base_path = Path(Path(__file__).parent.parent / 'data/co2_analysis')
    self._handler = '_' + handler.lower()
    validate_import_export_type(Co2AnalysisCatalogFactory, handler)
    self._path = base_path

  @property
  def _ecoinvent(self):
    """
    Retrieve Ecoinvent CO2 analysis catalog
    """
    return EcoinventCatalog(self._path)

  @property
  def catalog(self) -> Catalog:
    """
    Return a Co2Analysis catalog
    :return: Co2Analysis Catalog
    """
    _handlers = {
      '_ecoinvent': self._ecoinvent
    }
    return _handlers[self._handler]

