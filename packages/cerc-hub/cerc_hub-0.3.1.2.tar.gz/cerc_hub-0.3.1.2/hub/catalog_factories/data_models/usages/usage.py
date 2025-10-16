"""
Usage catalog usage
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
from typing import Union

from hub.catalog_factories.data_models.usages.appliances import Appliances
from hub.catalog_factories.data_models.usages.lighting import Lighting
from hub.catalog_factories.data_models.usages.occupancy import Occupancy
from hub.catalog_factories.data_models.usages.thermal_control import ThermalControl
from hub.catalog_factories.data_models.usages.domestic_hot_water import DomesticHotWater


class Usage:
  """
  Usage class
  """
  def __init__(self, name,
               hours_day,
               days_year,
               mechanical_air_change,
               ventilation_rate,
               occupancy,
               lighting,
               appliances,
               thermal_control,
               domestic_hot_water):
    self._name = name
    self._hours_day = hours_day
    self._days_year = days_year
    self._mechanical_air_change = mechanical_air_change
    self._ventilation_rate = ventilation_rate
    self._occupancy = occupancy
    self._lighting = lighting
    self._appliances = appliances
    self._thermal_control = thermal_control
    self._domestic_hot_water = domestic_hot_water

  @property
  def name(self) -> Union[None, str]:
    """
    Get usage zone usage name
    :return: None or str
    """
    return self._name

  @property
  def hours_day(self) -> Union[None, float]:
    """
    Get usage zone usage hours per day
    :return: None or float
    """
    return self._hours_day

  @property
  def days_year(self) -> Union[None, float]:
    """
    Get usage zone usage days per year
    :return: None or float
    """
    return self._days_year

  @property
  def mechanical_air_change(self) -> Union[None, float]:
    """
    Get usage zone mechanical air change in air change per second (1/s)
    :return: None or float
    """
    return self._mechanical_air_change

  @property
  def ventilation_rate(self) -> Union[None, float]:
    """
    Get usage zone ventilation rate in m3/m2s
    :return: None or float
    """
    return self._ventilation_rate

  @property
  def occupancy(self) -> Union[None, Occupancy]:
    """
    Get occupancy in the usage zone
    :return: None or Occupancy
    """
    return self._occupancy

  @property
  def lighting(self) -> Union[None, Lighting]:
    """
    Get lighting information
    :return: None or Lighting
    """
    return self._lighting

  @lighting.setter
  def lighting(self, value):
    """
    Set lighting information
    :param value: Lighting
    """
    self._lighting = value

  @property
  def appliances(self) -> Union[None, Appliances]:
    """
    Get appliances information
    :return: None or Appliances
    """
    return self._appliances

  @property
  def thermal_control(self) -> Union[None, ThermalControl]:
    """
    Get thermal control information
    :return: None or ThermalControl
    """
    return self._thermal_control

  @property
  def domestic_hot_water(self) -> Union[None, DomesticHotWater]:
    """
    Get domestic hot water information
    :return: None or DomesticHotWater
    """
    return self._domestic_hot_water

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Usage': {'name': self.name,
                         'hours a day': self.hours_day,
                         'days a year': self.days_year,
                         'mechanical air change [ACH]': self.mechanical_air_change,
                         'ventilation rate [m3/sm2]': self.ventilation_rate,
                         'occupancy': self.occupancy.to_dictionary(),
                         'lighting': self.lighting.to_dictionary(),
                         'appliances': self.appliances.to_dictionary(),
                         'thermal control': self.thermal_control.to_dictionary(),
                         'domestic hot water': self.domestic_hot_water.to_dictionary()
                         }
               }
    return content
