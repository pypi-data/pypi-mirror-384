"""
Dictionaries module for hub function to eilat construction function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class HubFunctionToEilatConstructionFunction:
  """
  Hub function to Eilat construction function class
  """
  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'Residential_building',
      cte.HOTEL: 'Residential_building',
      cte.DORMITORY: 'Residential_building',
      cte.DATACENTER: 'n/a',
      cte.FARM: 'n/a'
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
