"""
Dictionaries module for hub usage to Eilat usage
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class HubUsageToEilatUsage:
  """
  Hub usage to Eilat usage class
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'Residential',
      cte.HOTEL: 'Hotel employees',
      cte.DORMITORY: 'Dormitory',
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
