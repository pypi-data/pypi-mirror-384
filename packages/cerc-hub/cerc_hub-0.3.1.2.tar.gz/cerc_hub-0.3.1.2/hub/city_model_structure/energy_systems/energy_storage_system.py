"""
Energy storage system. Abstract class
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from abc import ABC


class EnergyStorageSystem(ABC):
  """
  Energy storage System class
  """
  def __init__(self):
    self._type_energy_stored = None
    self._storage_type = None
    self._model_name = None
    self._manufacturer = None
    self._nominal_capacity = None
    self._losses_ratio = None

  @property
  def type_energy_stored(self):
    """
    Get type of energy stored from ['electrical', 'thermal']
    :return: string
    """
    return self._type_energy_stored

  @type_energy_stored.setter
  def type_energy_stored(self, value):
    """
    Set type of energy stored from ['electrical', 'thermal']
    :return: string
    """
    self._type_energy_stored = value

  @property
  def storage_type(self):
    """
    Get storage type
    :return: string
    """
    return self._storage_type

  @storage_type.setter
  def storage_type(self, value):
    """
    Get storage type
    :param value: string
    """
    self._storage_type = value

  @property
  def model_name(self):
    """
    Get system model
    :return: string
    """
    return self._model_name

  @model_name.setter
  def model_name(self, value):
    """
    Set system model
    :param value: string
    """
    self._model_name = value

  @property
  def manufacturer(self):
    """
    Get name of manufacturer
    :return: string
    """
    return self._manufacturer

  @manufacturer.setter
  def manufacturer(self, value):
    """
    Set name of manufacturer
    :param value: string
    """
    self._manufacturer = value

  @property
  def nominal_capacity(self):
    """
    Get the nominal capacity of storage systems in Jules
    :return: float
    """
    return self._nominal_capacity

  @nominal_capacity.setter
  def nominal_capacity(self, value):
    """
    Set the nominal capacity of storage systems in Jules
    :return: float
    """
    self._nominal_capacity = value

  @property
  def losses_ratio(self):
    """
    Get the losses-ratio of storage system in Jules lost / Jules stored
    :return: float
    """
    return self._losses_ratio

  @losses_ratio.setter
  def losses_ratio(self, value):
    """
    Set the losses-ratio of storage system in Jules lost / Jules stored
    :return: float
    """
    self._losses_ratio = value
