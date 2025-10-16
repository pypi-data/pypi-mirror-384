"""
Energy System catalog heat generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from __future__ import annotations
from abc import ABC
from typing import List, Union

from hub.catalog_factories.data_models.energy_systems.energy_storage_system import EnergyStorageSystem
from hub.catalog_factories.data_models.energy_systems.distribution_system import DistributionSystem


class GenerationSystem(ABC):
  """
  Heat Generation system class
  """

  def __init__(self, system_id, name, model_name=None, manufacturer=None, fuel_type=None,
               distribution_systems=None, energy_storage_systems=None):
    self._system_id = system_id
    self._name = name
    self._model_name = model_name
    self._manufacturer = manufacturer
    self._fuel_type = fuel_type
    self._distribution_systems = distribution_systems
    self._energy_storage_systems = energy_storage_systems

  @property
  def id(self):
    """
    Get system id
    :return: float
    """
    return self._system_id

  @property
  def name(self):
    """
    Get system name
    :return: string
    """
    return self._name

  @property
  def system_type(self):
    """
    Get type
    :return: string
    """
    raise NotImplementedError

  @property
  def model_name(self):
    """
    Get system id
    :return: float
    """
    return self._model_name

  @property
  def manufacturer(self):
    """
    Get name
    :return: string
    """
    return self._manufacturer

  @property
  def fuel_type(self):
    """
    Get fuel_type from [renewable, gas, diesel, electricity, wood, coal, biogas]
    :return: string
    """
    return self._fuel_type

  @property
  def distribution_systems(self) -> Union[None, List[DistributionSystem]]:
    """
    Get distributions systems connected to this generation system
    :return: [DistributionSystem]
    """
    return self._distribution_systems

  @property
  def energy_storage_systems(self) -> Union[None, List[EnergyStorageSystem]]:
    """
    Get energy storage systems connected to this generation system
    :return: [EnergyStorageSystem]
    """
    return self._energy_storage_systems

  def to_dictionary(self):
    """Class content to dictionary"""
    raise NotImplementedError
