"""
Energy System catalog heat generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class NorthAmericaStorageSystemToHubEnergyStorage:
  """
  Montreal's system to hub energy generation system class
  """
  def __init__(self):
    self._dictionary = {
      'template Hot Water Storage Tank': cte.SENSIBLE,
                        }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
