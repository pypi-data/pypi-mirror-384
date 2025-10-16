"""
Dictionaries module for montreal custom fuel to hub fuel
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class MontrealCustomFuelToHubFuel:
  """
  Montreal custom fuel to hub fuel class
  """

  def __init__(self):
    self._dictionary = {
      'gas': cte.GAS,
      'natural gas': cte.GAS,
      'biomass': cte.BIOMASS,
      'electricity': cte.ELECTRICITY,
      'renewable': cte.RENEWABLE,
      'butane': cte.BUTANE,
      'diesel': cte.DIESEL
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
