"""
Dictionaries module for Palma function to hub function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Cecilia Pérez cperez@irec.cat
"""

import hub.helpers.constants as cte


class PalmaFunctionToHubFunction:
  """
  Palma function to hub function class
  """

  def __init__(self):
    self._dictionary = {'Residential': cte.RESIDENTIAL,
                        'Single-family building': cte.SINGLE_FAMILY_HOUSE,
                        'Large multifamily building': cte.HIGH_RISE_APARTMENT,
                        'Medium multifamily building': cte.MID_RISE_APARTMENT,
                        'Small multifamily building': cte.MULTI_FAMILY_HOUSE,
                        'V': cte.RESIDENTIAL
                        }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary