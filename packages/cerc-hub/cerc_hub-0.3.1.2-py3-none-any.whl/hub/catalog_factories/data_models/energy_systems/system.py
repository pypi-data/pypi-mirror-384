"""
Energy Systems catalog System
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from typing import Union, List
from pathlib import Path

from hub.catalog_factories.data_models.energy_systems.generation_system import GenerationSystem
from hub.catalog_factories.data_models.energy_systems.distribution_system import DistributionSystem


class System:
  """
  System class
  """

  def __init__(self,
               system_id,
               demand_types,
               name=None,
               generation_systems=None,
               distribution_systems=None,
               configuration_schema=None):
    self._system_id = system_id
    self._name = name
    self._demand_types = demand_types
    self._generation_systems = generation_systems
    self._distribution_systems = distribution_systems
    self._configuration_schema = configuration_schema

  @property
  def id(self):
    """
    Get equipment id
    :return: string
    """
    return self._system_id

  @property
  def name(self):
    """
    Get the system name
    :return: string
    """
    return self._name

  @property
  def demand_types(self):
    """
    Get demand able to cover from ['heating', 'cooling', 'domestic_hot_water', 'electricity']
    :return: [string]
    """
    return self._demand_types

  @property
  def generation_systems(self) -> Union[None, List[GenerationSystem]]:
    """
    Get generation systems
    :return: [GenerationSystem]
    """
    return self._generation_systems

  @property
  def distribution_systems(self) -> Union[None, List[DistributionSystem]]:
    """
    Get distribution systems
    :return: [DistributionSystem]
    """
    return self._distribution_systems

  @property
  def configuration_schema(self) -> Path:
    """
    Get system configuration schema
    :return: Path
    """
    return self._configuration_schema

  def to_dictionary(self):
    """Class content to dictionary"""
    _generation_systems = []
    for _generation in self.generation_systems:
      _generation_systems.append(_generation.to_dictionary())
    _distribution_systems = [_distribution.to_dictionary() for _distribution in
                             self.distribution_systems] if self.distribution_systems is not None else None

    content = {'system': {'id': self.id,
                          'name': self.name,
                          'demand types': self.demand_types,
                          'generation system(s)': _generation_systems,
                          'distribution system(s)': _distribution_systems,
                          'configuration schema path': self.configuration_schema
                          }
               }
    return content
