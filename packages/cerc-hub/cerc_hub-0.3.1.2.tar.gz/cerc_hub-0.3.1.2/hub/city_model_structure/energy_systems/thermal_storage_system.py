"""
Thermal storage system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from hub.city_model_structure.energy_systems.energy_storage_system import EnergyStorageSystem
from hub.city_model_structure.building_demand.layer import Layer


class ThermalStorageSystem(EnergyStorageSystem):
  """"
  Thermal Storage System Class
  """

  def __init__(self):

    super().__init__()
    self._volume = None
    self._height = None
    self._layers = None
    self._maximum_operating_temperature = None
    self._heating_coil_capacity = None
    self._temperature = None
    self._heating_coil_energy_consumption = None

  @property
  def volume(self):
    """
    Get the physical volume of the storage system in cubic meters
    :return: float
    """
    return self._volume

  @volume.setter
  def volume(self, value):
    """
    Set the physical volume of the storage system in cubic meters
    :param value: float
    """
    self._volume = value

  @property
  def height(self):
    """
    Get the diameter of the storage system in meters
    :return: float
    """
    return self._height

  @height.setter
  def height(self, value):
    """
    Set the diameter of the storage system in meters
    :param value: float
    """
    self._height = value

  @property
  def layers(self) -> [Layer]:
    """
    Get construction layers
    :return: [layer]
    """
    return self._layers

  @layers.setter
  def layers(self, value):
    """
    Set construction layers
    :param value: [layer]
    """
    self._layers = value

  @property
  def maximum_operating_temperature(self):
    """
    Get maximum operating temperature of the storage system in degree Celsius
    :return: float
    """
    return self._maximum_operating_temperature

  @maximum_operating_temperature.setter
  def maximum_operating_temperature(self, value):
    """
    Set maximum operating temperature of the storage system in degree Celsius
    :param value: float
    """
    self._maximum_operating_temperature = value

  @property
  def heating_coil_capacity(self):
    """
    Get heating coil capacity in Watts
    :return: float
    """
    return self._heating_coil_capacity

  @heating_coil_capacity.setter
  def heating_coil_capacity(self, value):
    """
    Set heating coil capacity in Watts
    :param value: float
    """
    self._heating_coil_capacity = value

  @property
  def temperature(self) -> dict:
    """
    Get fuel consumption in W, m3, or kg
    :return: dict{[float]}
    """
    return self._temperature

  @temperature.setter
  def temperature(self, value):
    """
    Set fuel consumption in W, m3, or kg
    :param value: dict{[float]}
    """
    self._temperature = value

  @property
  def heating_coil_energy_consumption(self) -> dict:
    """
    Get fuel consumption in W, m3, or kg
    :return: dict{[float]}
    """
    return self._heating_coil_energy_consumption

  @heating_coil_energy_consumption.setter
  def heating_coil_energy_consumption(self, value):
    """
    Set fuel consumption in W, m3, or kg
    :param value: dict{[float]}
    """
    self._heating_coil_energy_consumption = value
