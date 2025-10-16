"""
Cost catalog publish the life cycle cost
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Atiya atiya.atiya@mail.concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from pathlib import Path
from typing import TypeVar
from hub.catalog_factories.cost.montreal_custom_catalog import MontrealCustomCatalog

Catalog = TypeVar('Catalog')


class CostsCatalogFactory:
  """
  CostsCatalogFactory class
  """
  def __init__(self, file_type, base_path=None):
    if base_path is None:
      base_path = Path(Path(__file__).parent.parent / 'data/costs')
    self._catalog_type = '_' + file_type.lower()
    self._path = base_path

  @property
  def _montreal_custom(self):
    """
    Retrieve Montreal Custom catalog
    """
    return MontrealCustomCatalog(self._path)

  @property
  def catalog(self) -> Catalog:
    """
    Return a cost catalog
    :return: CostCatalog
    """
    return getattr(self, self._catalog_type, lambda: None)
