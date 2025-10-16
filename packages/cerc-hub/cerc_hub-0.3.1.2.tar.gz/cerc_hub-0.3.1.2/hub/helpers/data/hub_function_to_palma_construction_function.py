"""
Dictionaries module for hub function to Palma construction function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Cecilia Pérez cperez@irec.cat
"""

import hub.helpers.constants as cte


class HubFunctionToPalmaConstructionFunction:
  """
  Hub function to Palma construction function class
  """
  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'V',
      cte.SINGLE_FAMILY_HOUSE: 'Single-family building',
      cte.HIGH_RISE_APARTMENT: 'Large multifamily building',
      cte.MID_RISE_APARTMENT: 'Medium multifamily building',
      cte.MULTI_FAMILY_HOUSE: 'Small multifamily building'
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary