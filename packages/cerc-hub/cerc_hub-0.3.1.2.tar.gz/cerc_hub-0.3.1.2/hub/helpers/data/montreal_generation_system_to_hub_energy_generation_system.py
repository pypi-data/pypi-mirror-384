"""
Dictionaries module for Montreal system to hub energy generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class MontrealGenerationSystemToHubEnergyGenerationSystem:
  """
  Montreal's generation system to hub energy generation system class
  """
  def __init__(self):
    self._dictionary = {
      'boiler': cte.BOILER,
      'furnace': cte.FURNACE,
      'cooler': cte.CHILLER,
      'electricity generator': cte.ELECTRICITY_GENERATOR,
      'photovoltaic': cte.PHOTOVOLTAIC,
      'heat pump': cte.HEAT_PUMP,
      'joule': cte.JOULE,
      'split': cte.SPLIT,
      'butane heater': cte.BUTANE_HEATER

    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
