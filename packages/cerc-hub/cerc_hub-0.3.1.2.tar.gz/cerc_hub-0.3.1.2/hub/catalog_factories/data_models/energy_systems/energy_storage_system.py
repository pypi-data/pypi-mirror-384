"""
Energy System catalog heat generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from abc import ABC


class EnergyStorageSystem(ABC):
  """"
  Energy Storage System Abstract Class
  """

  def __init__(self, storage_id, model_name=None, manufacturer=None,
               nominal_capacity=None, losses_ratio=None):
    self._storage_id = storage_id
    self._model_name = model_name
    self._manufacturer = manufacturer
    self._nominal_capacity = nominal_capacity
    self._losses_ratio = losses_ratio

  @property
  def id(self):
    """
    Get storage id
    :return: string
    """
    return self._storage_id

  @property
  def type_energy_stored(self):
    """
    Get type of energy stored from ['electrical', 'thermal']
    :return: string
    """
    raise NotImplementedError

  @property
  def model_name(self):
    """
    Get system model
    :return: string
    """
    return self._model_name

  @property
  def manufacturer(self):
    """
    Get name of manufacturer
    :return: string
    """
    return self._manufacturer

  @property
  def nominal_capacity(self):
    """
    Get the nominal capacity of the storage system in Jules
    :return: float
    """
    return self._nominal_capacity

  @property
  def losses_ratio(self):
    """
    Get the losses-ratio of storage system in Jules lost / Jules stored
    :return: float
    """
    return self._losses_ratio

  def to_dictionary(self):
    """Class content to dictionary"""
    raise NotImplementedError
