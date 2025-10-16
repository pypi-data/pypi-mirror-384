"""
Cost item properties
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import Union


class ItemDescription:
  """
  Item description class
  """
  def __init__(self, item_type,
               initial_investment=None,
               initial_investment_unit=None,
               refurbishment=None,
               refurbishment_unit=None,
               reposition=None,
               reposition_unit=None,
               lifetime=None):

    self._item_type = item_type
    self._initial_investment = initial_investment
    self._initial_investment_unit = initial_investment_unit
    self._refurbishment = refurbishment
    self._refurbishment_unit = refurbishment_unit
    self._reposition = reposition
    self._reposition_unit = reposition_unit
    self._lifetime = lifetime

  @property
  def type(self):
    """
    Get item type
    :return: str
    """
    return self._item_type

  @property
  def initial_investment(self) -> Union[tuple[None, None], tuple[float, str]]:
    """
    Get initial investment of the specific item in given units
    :return: None, None or float, str
    """
    return self._initial_investment, self._initial_investment_unit

  @property
  def refurbishment(self) -> Union[tuple[None, None], tuple[float, str]]:
    """
    Get refurbishment costs of the specific item in given units
    :return: None, None or float, str
    """
    return self._refurbishment, self._refurbishment_unit

  @property
  def reposition(self) -> Union[tuple[None, None], tuple[float, str]]:
    """
    Get reposition costs of the specific item in given units
    :return: None, None or float, str
    """
    return self._reposition, self._reposition_unit

  @property
  def lifetime(self) -> Union[None, float]:
    """
    Get lifetime in years
    :return: None or float
    """
    return self._lifetime

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Item': {'type': self.type,
                        'initial investment': self.initial_investment[0],
                        'initial investment units': self.initial_investment[1],
                        'refurbishment': self.refurbishment[0],
                        'refurbishment units': self.refurbishment[1],
                        'reposition': self.reposition[0],
                        'reposition units': self.reposition[1],
                        'life time [years]': self.lifetime
                        }
               }

    return content
