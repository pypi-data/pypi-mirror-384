"""
Dictionaries module for Eilat function to hub function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class EilatFunctionToHubFunction:
  """
  Eilat function to hub function class
  """

  def __init__(self):
    self._dictionary = {'Residential': cte.RESIDENTIAL,
                        'Dormitory': cte.DORMITORY,
                        'Hotel employ': cte.HOTEL
                        }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
