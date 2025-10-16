"""
Energy system definition
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import Union, List
from pathlib import Path

from hub.city_model_structure.energy_systems.distribution_system import DistributionSystem
from hub.city_model_structure.energy_systems.non_pv_generation_system import NonPvGenerationSystem
from hub.city_model_structure.energy_systems.pv_generation_system import PvGenerationSystem
from hub.city_model_structure.energy_systems.control_system import ControlSystem
from hub.city_model_structure.city_object import CityObject


class EnergySystem:
  """
  EnergySystem class
  """
  def __init__(self):
    self._demand_types = None
    self._name = None
    self._generation_systems = None
    self._distribution_systems = None
    self._configuration_schema = None
    self._connected_city_objects = None
    self._control_system = None

  @property
  def demand_types(self):
    """
    Get demand able to cover from [Heating, Cooling, Domestic Hot Water, Electricity]
    :return: [string]
    """
    return self._demand_types

  @demand_types.setter
  def demand_types(self, value):
    """
    Set demand able to cover from [Heating, Cooling, Domestic Hot Water, Electricity]
    :param value: [string]
    """
    self._demand_types = value

  @property
  def name(self):
    """
    Get energy system name
    :return: str
    """
    return self._name

  @name.setter
  def name(self, value):
    """
    Set energy system name
    :param value:
    """
    self._name = value

  @property
  def generation_systems(self) -> Union[List[NonPvGenerationSystem], List[PvGenerationSystem]]:
    """
    Get generation systems
    :return: [GenerationSystem]
    """
    return self._generation_systems

  @generation_systems.setter
  def generation_systems(self, value):
    """
    Set generation systems
    :return: [GenerationSystem]
    """
    self._generation_systems = value

  @property
  def distribution_systems(self) -> Union[None, List[DistributionSystem]]:
    """
    Get distribution systems
    :return: [DistributionSystem]
    """
    return self._distribution_systems

  @distribution_systems.setter
  def distribution_systems(self, value):
    """
    Set distribution systems
    :param value: [DistributionSystem]
    """
    self._distribution_systems = value

  @property
  def configuration_schema(self) -> Path:
    """
    Get the schema of the system configuration
    :return: Path
    """
    return self._configuration_schema

  @configuration_schema.setter
  def configuration_schema(self, value):
    """
    Set the schema of the system configuration
    :param value: Path
    """
    self._configuration_schema = value

  @property
  def connected_city_objects(self) -> Union[None, List[CityObject]]:
    """
    Get list of city objects that are connected to this energy system
    :return: [CityObject]
    """
    return self._connected_city_objects

  @connected_city_objects.setter
  def connected_city_objects(self, value):
    """
    Set list of city objects that are connected to this energy system
    :param value: [CityObject]
    """
    self._connected_city_objects = value

  @property
  def control_system(self) -> Union[None, ControlSystem]:
    """
    Get control system of the energy system
    :return: ControlSystem
    """
    return self._control_system

  @control_system.setter
  def control_system(self, value):
    """
    Set control system of the energy system
    :param value: ControlSystem
    """
    self._control_system = value
