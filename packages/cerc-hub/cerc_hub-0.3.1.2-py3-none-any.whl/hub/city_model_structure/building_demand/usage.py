"""
Usage module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import uuid
from typing import Union, List
import hub.helpers.constants as cte
from hub.city_model_structure.building_demand.occupancy import Occupancy
from hub.city_model_structure.building_demand.lighting import Lighting
from hub.city_model_structure.building_demand.appliances import Appliances
from hub.city_model_structure.building_demand.thermal_control import ThermalControl
from hub.city_model_structure.building_demand.domestic_hot_water import DomesticHotWater
from hub.city_model_structure.building_demand.internal_gain import InternalGain


class Usage:
  """
  Usage class
  """
  def __init__(self):
    self._id = None
    self._name = None
    self._percentage = None
    self._internal_gains = None
    self._hours_day = None
    self._days_year = None
    self._mechanical_air_change = None
    self._occupancy = None
    self._lighting = None
    self._appliances = None
    self._thermal_control = None
    self._domestic_hot_water = None

  @property
  def id(self):
    """
    Get usage zone id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def name(self) -> Union[None, str]:
    """
    Get usage zone usage
    :return: None or str
    """
    return self._name

  @name.setter
  def name(self, value):
    """
    Set usage zone usage
    :param value: str
    """
    if value is not None:
      self._name = str(value)

  @property
  def percentage(self):
    """
    Get usage zone percentage in range[0,1]
    :return: float
    """
    return self._percentage

  @percentage.setter
  def percentage(self, value):
    """
    Set usage zone percentage in range[0,1]
    :param value: float
    """
    if value is not None:
      self._percentage = float(value)

  @property
  def internal_gains(self) -> List[InternalGain]:
    """
    Calculates and returns the list of all internal gains defined
    :return: InternalGains
    """
    if self._internal_gains is None:
      if self.occupancy is not None:
        if self.occupancy.latent_internal_gain is not None:
          _internal_gain = InternalGain()
          _internal_gain.type = cte.OCCUPANCY
          _total_heat_gain = (self.occupancy.sensible_convective_internal_gain
                              + self.occupancy.sensible_radiative_internal_gain
                              + self.occupancy.latent_internal_gain)
          _internal_gain.average_internal_gain = _total_heat_gain
          _internal_gain.latent_fraction = 0
          _internal_gain.radiative_fraction = 0
          _internal_gain.convective_fraction = 0
          if _total_heat_gain != 0:
            _internal_gain.latent_fraction = self.occupancy.latent_internal_gain / _total_heat_gain
            _internal_gain.radiative_fraction = self.occupancy.sensible_radiative_internal_gain / _total_heat_gain
            _internal_gain.convective_fraction = self.occupancy.sensible_convective_internal_gain / _total_heat_gain
          _internal_gain.schedules = self.occupancy.occupancy_schedules
          self._internal_gains = [_internal_gain]
      if self.lighting is not None:
        _internal_gain = InternalGain()
        _internal_gain.type = cte.LIGHTING
        _internal_gain.average_internal_gain = self.lighting.density
        _internal_gain.latent_fraction = self.lighting.latent_fraction
        _internal_gain.radiative_fraction = self.lighting.radiative_fraction
        _internal_gain.convective_fraction = self.lighting.convective_fraction
        _internal_gain.schedules = self.lighting.schedules
        if self._internal_gains is not None:
          self._internal_gains.append(_internal_gain)
        else:
          self._internal_gains = [_internal_gain]
      if self.appliances is not None:
        _internal_gain = InternalGain()
        _internal_gain.type = cte.APPLIANCES
        _internal_gain.average_internal_gain = self.appliances.density
        _internal_gain.latent_fraction = self.appliances.latent_fraction
        _internal_gain.radiative_fraction = self.appliances.radiative_fraction
        _internal_gain.convective_fraction = self.appliances.convective_fraction
        _internal_gain.schedules = self.appliances.schedules
        if self._internal_gains is not None:
          self._internal_gains.append(_internal_gain)
        else:
          self._internal_gains = [_internal_gain]
    return self._internal_gains

  @internal_gains.setter
  def internal_gains(self, value):
    """
    Set usage zone internal gains
    :param value: [InternalGain]
    """
    self._internal_gains = value

  @property
  def hours_day(self) -> Union[None, float]:
    """
    Get usage zone usage hours per day
    :return: None or float
    """
    return self._hours_day

  @hours_day.setter
  def hours_day(self, value):
    """
    Set usage zone usage hours per day
    :param value: float
    """
    if value is not None:
      self._hours_day = float(value)

  @property
  def days_year(self) -> Union[None, float]:
    """
    Get usage zone usage days per year
    :return: None or float
    """
    return self._days_year

  @days_year.setter
  def days_year(self, value):
    """
    Set usage zone usage days per year
    :param value: float
    """
    if value is not None:
      self._days_year = float(value)

  @property
  def mechanical_air_change(self) -> Union[None, float]:
    """
    Get usage zone mechanical air change in air change per second (1/s)
    :return: None or float
    """
    return self._mechanical_air_change

  @mechanical_air_change.setter
  def mechanical_air_change(self, value):
    """
    Set usage zone mechanical air change in air change per second (1/s)
    :param value: float
    """
    if value is not None:
      self._mechanical_air_change = float(value)

  @property
  def occupancy(self) -> Union[None, Occupancy]:
    """
    Get occupancy in the usage zone
    :return: None or Occupancy
    """
    return self._occupancy

  @occupancy.setter
  def occupancy(self, value):
    """
    Set occupancy in the usage zone
    :param value: Occupancy
    """
    self._occupancy = value

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

  @appliances.setter
  def appliances(self, value):
    """
    Set appliances information
    :param value: Appliances
    """
    self._appliances = value

  @property
  def thermal_control(self) -> Union[None, ThermalControl]:
    """
    Get thermal control information
    :return: None or ThermalControl
    """
    return self._thermal_control

  @thermal_control.setter
  def thermal_control(self, value):
    """
    Set thermal control information
    :param value: ThermalControl
    """
    self._thermal_control = value

  @property
  def domestic_hot_water(self) -> Union[None, DomesticHotWater]:
    """
    Get domestic hot water information
    :return: None or ThermalControl
    """
    return self._domestic_hot_water

  @domestic_hot_water.setter
  def domestic_hot_water(self, value):
    """
    Set domestic hot water information
    :return: None or ThermalControl
    """
    self._domestic_hot_water = value
