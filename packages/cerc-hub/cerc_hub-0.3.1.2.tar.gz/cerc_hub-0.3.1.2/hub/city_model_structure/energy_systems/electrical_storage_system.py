"""
Electrical storage system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.city_model_structure.energy_systems.energy_storage_system import EnergyStorageSystem


class ElectricalStorageSystem(EnergyStorageSystem):
  """"
  Electrical Storage System Class
  """

  def __init__(self):

    super().__init__()
    self._rated_output_power = None
    self._nominal_efficiency = None
    self._battery_voltage = None
    self._depth_of_discharge = None
    self._self_discharge_rate = None

  @property
  def rated_output_power(self):
    """
    Get the rated output power of storage system in Watts
    :return: float
    """
    return self._rated_output_power

  @rated_output_power.setter
  def rated_output_power(self, value):
    """
    Set the rated output power of storage system in Watts
    :param value: float
    """
    self._rated_output_power = value

  @property
  def nominal_efficiency(self):
    """
    Get the nominal efficiency of the storage system
    :return: float
    """
    return self._nominal_efficiency

  @nominal_efficiency.setter
  def nominal_efficiency(self, value):
    """
    Set the nominal efficiency of the storage system
    :param value: float
    """
    self._nominal_efficiency = value

  @property
  def battery_voltage(self):
    """
    Get the battery voltage in Volts
    :return: float
    """
    return self._battery_voltage

  @battery_voltage.setter
  def battery_voltage(self, value):
    """
    Set the battery voltage in Volts
    :param value: float
    """
    self._battery_voltage = value

  @property
  def depth_of_discharge(self):
    """
    Get the depth of discharge as a percentage
    :return: float
    """
    return self._depth_of_discharge

  @depth_of_discharge.setter
  def depth_of_discharge(self, value):
    """
    Set the depth of discharge as a percentage
    :param value: float
    """
    self._depth_of_discharge = value

  @property
  def self_discharge_rate(self):
    """
    Get the self discharge rate of battery as a percentage
    :return: float
    """
    return self._self_discharge_rate

  @self_discharge_rate.setter
  def self_discharge_rate(self, value):
    """
    Set the self discharge rate of battery as a percentage
    :param value: float
    """
    self._self_discharge_rate = value
