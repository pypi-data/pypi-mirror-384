"""
Archetype catalog Cost
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.catalog_factories.data_models.cost.capital_cost import CapitalCost
from hub.catalog_factories.data_models.cost.operational_cost import OperationalCost
from hub.catalog_factories.data_models.cost.income import Income


class Archetype:
  """
  Archetype class
  """
  def __init__(self,
               lod,
               function,
               municipality,
               country,
               currency,
               capital_cost,
               operational_cost,
               end_of_life_cost,
               income):

    self._lod = lod
    self._function = function
    self._municipality = municipality
    self._country = country
    self._currency = currency
    self._capital_cost = capital_cost
    self._operational_cost = operational_cost
    self._end_of_life_cost = end_of_life_cost
    self._income = income

  @property
  def name(self):
    """
    Get name
    :return: string
    """
    return f'{self._country}_{self._municipality}_{self._function}_lod{self._lod}'

  @property
  def lod(self):
    """
    Get level of detail of the catalog
    :return: string
    """
    return self._lod

  @property
  def function(self):
    """
    Get function
    :return: string
    """
    return self._function

  @property
  def municipality(self):
    """
    Get municipality
    :return: string
    """
    return self._municipality

  @property
  def country(self):
    """
    Get country
    :return: string
    """
    return self._country

  @property
  def currency(self):
    """
    Get currency
    :return: string
    """
    return self._currency

  @property
  def capital_cost(self) -> CapitalCost:
    """
    Get capital cost
    :return: CapitalCost
    """
    return self._capital_cost

  @property
  def operational_cost(self) -> OperationalCost:
    """
    Get operational cost
    :return: OperationalCost
    """
    return self._operational_cost

  @property
  def end_of_life_cost(self):
    """
    Get end of life cost in given currency per m2
    :return: float
    """
    return self._end_of_life_cost

  @property
  def income(self) -> Income:
    """
    Get income
    :return: Income
    """
    return self._income

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Archetype': {'name': self.name,
                             'level of detail': self.lod,
                             'municipality': self.municipality,
                             'country': self.country,
                             'currency': self.currency,
                             'function': self.function,
                             'capital cost': self.capital_cost.to_dictionary(),
                             'operational cost': self.operational_cost.to_dictionary(),
                             'end of life cost [currency/m2]': self.end_of_life_cost,
                             'income': self.income.to_dictionary()
                             }
               }
    return content
