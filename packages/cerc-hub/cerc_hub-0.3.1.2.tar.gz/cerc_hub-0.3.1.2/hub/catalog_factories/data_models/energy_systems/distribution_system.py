"""
Energy System catalog distribution system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from typing import Union, List, TypeVar

from hub.catalog_factories.data_models.energy_systems.energy_storage_system import EnergyStorageSystem
from hub.catalog_factories.data_models.energy_systems.emission_system import EmissionSystem

GenerationSystem = TypeVar('GenerationSystem')


class DistributionSystem:
  """
  Distribution system class
  """

  def __init__(self, system_id, model_name=None, system_type=None, supply_temperature=None,
               distribution_consumption_fix_flow=None, distribution_consumption_variable_flow=None, heat_losses=None,
               generation_systems=None, energy_storage_systems=None, emission_systems=None):
    self._system_id = system_id
    self._model_name = model_name
    self._type = system_type
    self._supply_temperature = supply_temperature
    self._distribution_consumption_fix_flow = distribution_consumption_fix_flow
    self._distribution_consumption_variable_flow = distribution_consumption_variable_flow
    self._heat_losses = heat_losses
    self._generation_systems = generation_systems
    self._energy_storage_systems = energy_storage_systems
    self._emission_systems = emission_systems

  @property
  def id(self):
    """
    Get system id
    :return: float
    """
    return self._system_id

  @property
  def model_name(self):
    """
    Get model name
    :return: string
    """
    return self._model_name

  @property
  def type(self):
    """
    Get type from [air, water, refrigerant]
    :return: string
    """
    return self._type

  @property
  def supply_temperature(self):
    """
    Get supply_temperature in degree Celsius
    :return: float
    """
    return self._supply_temperature

  @property
  def distribution_consumption_fix_flow(self):
    """
    Get distribution_consumption if the pump or fan work at fix mass or volume flow in ratio over peak power (W/W)
    :return: float
    """
    return self._distribution_consumption_fix_flow

  @property
  def distribution_consumption_variable_flow(self):
    """
    Get distribution_consumption if the pump or fan work at variable mass or volume flow in ratio
    over energy produced (J/J)
    :return: float
    """
    return self._distribution_consumption_variable_flow

  @property
  def heat_losses(self):
    """
    Get heat_losses in ratio over energy produced in J/J
    :return: float
    """
    return self._heat_losses

  @property
  def generation_systems(self) -> Union[None, List[GenerationSystem]]:
    """
    Get generation systems connected to the distribution system
    :return: [GenerationSystem]
    """
    return self._generation_systems

  @property
  def energy_storage_systems(self) -> Union[None, List[EnergyStorageSystem]]:
    """
    Get energy storage systems connected to this distribution system
    :return: [EnergyStorageSystem]
    """
    return self._energy_storage_systems

  @property
  def emission_systems(self) -> Union[None, List[EmissionSystem]]:
    """
    Get energy emission systems connected to this distribution system
    :return: [EmissionSystem]
    """
    return self._emission_systems

  def to_dictionary(self):
    """Class content to dictionary"""
    _generation_systems = [_generation_system.to_dictionary() for _generation_system in
                           self.generation_systems] if self.generation_systems is not None else None
    _energy_storage_systems = [_energy_storage_system.to_dictionary() for _energy_storage_system in
                               self.energy_storage_systems] if self.energy_storage_systems is not None else None
    _emission_systems = [_emission_system.to_dictionary() for _emission_system in
                         self.emission_systems] if self.emission_systems is not None else None

    content = {
      'Layer': {
        'id': self.id,
        'model name': self.model_name,
        'type': self.type,
        'supply temperature [Celsius]': self.supply_temperature,
        'distribution consumption if fix flow over peak power [W/W]': self.distribution_consumption_fix_flow,
        'distribution consumption if variable flow over peak power [J/J]': self.distribution_consumption_variable_flow,
        'heat losses per energy produced [J/J]': self.heat_losses,
        'generation systems connected': _generation_systems,
        'energy storage systems connected': _energy_storage_systems,
        'emission systems connected': _emission_systems
      }
    }
    return content
