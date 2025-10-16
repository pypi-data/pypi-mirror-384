"""
Energy generation system (abstract class)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from __future__ import annotations
from abc import ABC
from typing import Union, List

from hub.city_model_structure.energy_systems.distribution_system import DistributionSystem
from hub.city_model_structure.energy_systems.thermal_storage_system import ThermalStorageSystem
from hub.city_model_structure.energy_systems.electrical_storage_system import ElectricalStorageSystem


class GenerationSystem(ABC):
  """
  GenerationSystem class
  """
  def __init__(self):
    self._system_type = None
    self._name = None
    self._model_name = None
    self._manufacturer = None
    self._fuel_type = None
    self._distribution_systems = None
    self._energy_storage_systems = None
    self._number_of_units = None

  @property
  def system_type(self):
    """
    Get type
    :return: string
    """
    return self._system_type

  @system_type.setter
  def system_type(self, value):
    """
    Set type
    :param value: string
    """
    self._system_type = value

  @property
  def name(self):
    """
    Get name
    :return: string
    """
    return self._name

  @name.setter
  def name(self, value):
    """
    Set name
    :param value: string
    """
    self._name = value

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
  def manufacturer(self):
    """
    Get manufacturer's name
    :return: string
    """
    return self._manufacturer

  @manufacturer.setter
  def manufacturer(self, value):
    """
    Set manufacturer's name
    :param value: string
    """
    self._manufacturer = value

  @property
  def fuel_type(self):
    """
    Get fuel_type from [Renewable, Gas, Diesel, Electricity, Wood, Coal]
    :return: string
    """
    return self._fuel_type

  @fuel_type.setter
  def fuel_type(self, value):
    """
    Set fuel_type from [Renewable, Gas, Diesel, Electricity, Wood, Coal]
    :param value: string
    """
    self._fuel_type = value

  @property
  def distribution_systems(self) -> Union[None, List[DistributionSystem]]:
    """
    Get distributions systems connected to this generation system
    :return: [DistributionSystem]
    """
    return self._distribution_systems

  @distribution_systems.setter
  def distribution_systems(self, value):
    """
    Set distributions systems connected to this generation system
    :param value: [DistributionSystem]
    """
    self._distribution_systems = value

  @property
  def energy_storage_systems(self) -> Union[None, List[ThermalStorageSystem], List[ElectricalStorageSystem]]:
    """
    Get energy storage systems connected to this generation system
    :return: [EnergyStorageSystem]
    """
    return self._energy_storage_systems

  @energy_storage_systems.setter
  def energy_storage_systems(self, value):
    """
    Set energy storage systems connected to this generation system
    :param value: [EnergyStorageSystem]
    """
    self._energy_storage_systems = value

  @property
  def number_of_units(self):
    """
    Get number of a specific generation unit
    :return: int
    """
    return self._number_of_units

  @number_of_units.setter
  def number_of_units(self, value):
    """
    Set number of a specific generation unit
    :return: int
    """
    self._number_of_units = value
