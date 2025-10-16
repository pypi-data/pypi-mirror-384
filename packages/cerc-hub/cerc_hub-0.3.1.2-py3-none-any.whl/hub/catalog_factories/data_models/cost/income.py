"""
Incomes included in the costs catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import Union


class Income:
  """
  Income class
  """
  def __init__(self, construction_subsidy=None,
               hvac_subsidy=None,
               photovoltaic_subsidy=None,
               electricity_export=None,
               reductions_tax=None):

    self._construction_subsidy = construction_subsidy
    self._hvac_subsidy = hvac_subsidy
    self._photovoltaic_subsidy = photovoltaic_subsidy
    self._electricity_export = electricity_export
    self._reductions_tax = reductions_tax

  @property
  def construction_subsidy(self) -> Union[None, float]:
    """
    Get subsidy for construction in percentage %
    :return: None or float
    """
    return self._construction_subsidy

  @property
  def hvac_subsidy(self) -> Union[None, float]:
    """
    Get subsidy for HVAC system in percentage %
    :return: None or float
    """
    return self._hvac_subsidy

  @property
  def photovoltaic_subsidy(self) -> Union[None, float]:
    """
    Get subsidy PV systems in percentage
    :return: None or float
    """
    return self._photovoltaic_subsidy

  @property
  def electricity_export(self) -> Union[None, float]:
    """
    Get electricity export incomes in currency per J
    :return: None or float
    """
    return self._electricity_export

  @property
  def reductions_tax(self) -> Union[None, float]:
    """
    Get reduction in taxes in percentage (-)
    :return: None or float
    """
    return self._reductions_tax

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Income': {'construction subsidy [%]': self.construction_subsidy,
                          'hvac subsidy [%]': self.hvac_subsidy,
                          'photovoltaic subsidy [%]': self.photovoltaic_subsidy,
                          'electricity export [currency/J]': self.electricity_export,
                          'reductions tax': self.reductions_tax
                          }
               }

    return content
