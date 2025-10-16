"""
Energy Systems catalog factory, publish the energy systems information
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Álvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from pathlib import Path
from typing import TypeVar

from hub.catalog_factories.energy_systems.montreal_custom_catalog import MontrealCustomCatalog
from hub.catalog_factories.energy_systems.montreal_future_system_catalogue import MontrealFutureSystemCatalogue
from hub.catalog_factories.energy_systems.palma_system_catalgue import PalmaSystemCatalogue
from hub.helpers.utils import validate_import_export_type

Catalog = TypeVar('Catalog')


class EnergySystemsCatalogFactory:
  """
  Energy system catalog factory class
  """
  def __init__(self, handler, base_path=None):
    if base_path is None:
      base_path = Path(Path(__file__).parent.parent / 'data/energy_systems')
    self._handler = '_' + handler.lower()
    validate_import_export_type(EnergySystemsCatalogFactory, handler)
    self._path = base_path

  @property
  def _montreal_custom(self):
    """
    Retrieve NRCAN catalog
    """
    return MontrealCustomCatalog(self._path)

  @property
  def _montreal_future(self):
    """
    Retrieve North American catalog
    """
    return MontrealFutureSystemCatalogue(self._path)

  @property
  def _palma(self):
    """
    Retrieve Palma catalog
    """
    return PalmaSystemCatalogue(self._path)

  @property
  def catalog(self) -> Catalog:
    """
    Enrich the city given to the class using the class given handler
    :return: Catalog
    """
    return getattr(self, self._handler, lambda: None)
