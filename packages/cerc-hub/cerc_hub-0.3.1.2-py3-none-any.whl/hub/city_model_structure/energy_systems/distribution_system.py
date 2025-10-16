"""
Energy distribution system definition
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import Union, List, TypeVar

from hub.city_model_structure.energy_systems.emission_system import EmissionSystem
from hub.city_model_structure.energy_systems.energy_storage_system import EnergyStorageSystem

GenerationSystem = TypeVar('GenerationSystem')


class DistributionSystem:
  """
  DistributionSystem class
  """
  def __init__(self):
    self._model_name = None
    self._type = None
    self._supply_temperature = None
    self._distribution_consumption_fix_flow = None
    self._distribution_consumption_variable_flow = None
    self._heat_losses = None
    self._generation_systems = None
    self._energy_storage_systems = None
    self._emission_systems = None

  @property
  def model_name(self):
    """
    Get model name
    :return: string
    """
    return self._model_name

  @model_name.setter
  def model_name(self, value):
    """
    Set model name
    :param value: string
    """
    self._model_name = value

  @property
  def type(self):
    """
    Get type from [air, water, refrigerant]
    :return: string
    """
    return self._type

  @type.setter
  def type(self, value):
    """
    Set type from [air, water, refrigerant]
    :param value: string
    """
    self._type = value

  @property
  def supply_temperature(self):
    """
    Get supply_temperature in degree Celsius
    :return: float
    """
    return self._supply_temperature

  @supply_temperature.setter
  def supply_temperature(self, value):
    """
    Set supply_temperature in degree Celsius
    :param value: float
    """
    self._supply_temperature = value

  @property
  def distribution_consumption_fix_flow(self):
    """
    Get distribution_consumption if the pump or fan work at fix mass or volume flow in ratio over peak power (W/W)
    :return: float
    """
    return self._distribution_consumption_fix_flow

  @distribution_consumption_fix_flow.setter
  def distribution_consumption_fix_flow(self, value):
    """
    Set distribution_consumption if the pump or fan work at fix mass or volume flow in ratio over peak power (W/W)
    :return: float
    """
    self._distribution_consumption_fix_flow = value

  @property
  def distribution_consumption_variable_flow(self):
    """
    Get distribution_consumption if the pump or fan work at variable mass or volume flow in ratio
    over energy produced (J/J)
    :return: float
    """
    return self._distribution_consumption_variable_flow

  @distribution_consumption_variable_flow.setter
  def distribution_consumption_variable_flow(self, value):
    """
    Set distribution_consumption if the pump or fan work at variable mass or volume flow in ratio
    over energy produced (J/J)
    :return: float
    """
    self._distribution_consumption_variable_flow = value

  @property
  def heat_losses(self):
    """
    Get heat_losses in ratio over energy produced
    :return: float
    """
    return self._heat_losses

  @heat_losses.setter
  def heat_losses(self, value):
    """
    Set heat_losses in ratio over energy produced
    :param value: float
    """
    self._heat_losses = value

  @property
  def generation_systems(self) -> Union[None, List[GenerationSystem]]:
    """
    Get generation systems connected to the distribution system
    :return: [GenerationSystem]
    """
    return self._generation_systems

  @generation_systems.setter
  def generation_systems(self, value):
    """
    Set generation systems connected to the distribution system
    :param value: [GenerationSystem]
    """
    self._generation_systems = value

  @property
  def energy_storage_systems(self) -> Union[None, List[EnergyStorageSystem]]:
    """
    Get energy storage systems connected to this distribution system
    :return: [EnergyStorageSystem]
    """
    return self._energy_storage_systems

  @energy_storage_systems.setter
  def energy_storage_systems(self, value):
    """
    Set energy storage systems connected to this distribution system
    :param value: [EnergyStorageSystem]
    """
    self._energy_storage_systems = value

  @property
  def emission_systems(self) -> Union[None, List[EmissionSystem]]:
    """
    Get energy emission systems connected to this distribution system
    :return: [EmissionSystem]
    """
    return self._emission_systems

  @emission_systems.setter
  def emission_systems(self, value):
    """
    Set energy emission systems connected to this distribution system
    :param value: [EmissionSystem]
    """
    self._emission_systems = value
