"""
Dictionaries module for Montreal system catalog demand types to hub energy demand types
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class MontrealDemandTypeToHubEnergyDemandType:
  """
  Montreal demand type to hub energy demand type
  """
  def __init__(self):
    self._dictionary = {'heating': cte.HEATING,
                        'cooling': cte.COOLING,
                        'domestic_hot_water': cte.DOMESTIC_HOT_WATER,
                        'electricity': cte.ELECTRICITY,
                        }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
