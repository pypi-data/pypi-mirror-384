"""
Operational costs included in the catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List
from hub.catalog_factories.data_models.cost.fuel import Fuel


class OperationalCost:
  """
  Operational cost class
  """
  def __init__(self, fuels, maintenance_heating, maintenance_cooling, maintenance_pv, co2):
    self._fuels = fuels
    self._maintenance_heating = maintenance_heating
    self._maintenance_cooling = maintenance_cooling
    self._maintenance_pv = maintenance_pv
    self._co2 = co2

  @property
  def fuels(self) -> List[Fuel]:
    """
    Get fuels listed in capital costs
    :return: [Fuel]
    """
    return self._fuels

  @property
  def maintenance_heating(self):
    """
    Get cost of maintaining the heating system in currency/W
    :return: float
    """
    return self._maintenance_heating

  @property
  def maintenance_cooling(self):
    """
    Get cost of maintaining the cooling system in currency/W
    :return: float
    """
    return self._maintenance_cooling

  @property
  def maintenance_pv(self):
    """
    Get cost of maintaining the PV system in currency/m2
    :return: float
    """
    return self._maintenance_pv

  @property
  def co2(self):
    """
    Get cost of CO2 emissions in currency/kgCO2
    :return: float
    """
    return self._co2

  def to_dictionary(self):
    """Class content to dictionary"""
    _fuels = []
    for _fuel in self.fuels:
      _fuels.append(_fuel.to_dictionary())
    content = {'Maintenance': {'fuels': _fuels,
                               'cost of maintaining the heating system [currency/W]': self.maintenance_heating,
                               'cost of maintaining the cooling system [currency/W]': self.maintenance_cooling,
                               'cost of maintaining the PV system [currency/W]': self.maintenance_pv,
                               'cost of CO2 emissions [currency/kgCO2]': self.co2
                               }
               }

    return content
