"""
Cost fuel
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import Union


class Fuel:
  """
  Fuel class
  """
  def __init__(self, fuel_type,
               fixed_monthly=None,
               fixed_power=None,
               variable=None,
               variable_units=None):

    self._fuel_type = fuel_type
    self._fixed_monthly = fixed_monthly
    self._fixed_power = fixed_power
    self._variable = variable
    self._variable_units = variable_units

  @property
  def type(self):
    """
    Get fuel type
    :return: str
    """
    return self._fuel_type

  @property
  def fixed_monthly(self) -> Union[None, float]:
    """
    Get fixed operational costs in currency per month
    :return: None or float
    """
    return self._fixed_monthly

  @property
  def fixed_power(self) -> Union[None, float]:
    """
    Get fixed operational costs depending on the peak power consumed in currency per month per W
    :return: None or float
    """
    if self._fixed_power is not None:
      return self._fixed_power/1000
    return None

  @property
  def variable(self) -> Union[tuple[None, None], tuple[float, str]]:
    """
    Get variable costs in given units
    :return: None, None or float, str
    """
    return self._variable, self._variable_units

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Fuel': {'fuel type': self.type,
                        'fixed operational costs [currency/month]': self.fixed_monthly,
                        'fixed operational costs depending on the peak power consumed [currency/month W]': self.fixed_power,
                        'variable operational costs': self.variable[0],
                        'units': self.variable[1]
                        }
               }

    return content
