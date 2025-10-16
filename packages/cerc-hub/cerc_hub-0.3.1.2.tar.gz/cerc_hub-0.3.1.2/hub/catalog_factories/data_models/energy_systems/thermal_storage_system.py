"""
Energy System catalog thermal storage system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from hub.catalog_factories.data_models.energy_systems.energy_storage_system import EnergyStorageSystem
from hub.catalog_factories.data_models.construction.layer import Layer
from hub.catalog_factories.data_models.construction.material import Material

class ThermalStorageSystem(EnergyStorageSystem):
  """"
  Energy Storage System Class
  """

  def __init__(self, storage_id, type_energy_stored=None, model_name=None, manufacturer=None, storage_type=None,
               nominal_capacity=None, losses_ratio=None, volume=None, height=None, layers=None,
               maximum_operating_temperature=None, storage_medium=None, heating_coil_capacity=None):

    super().__init__(storage_id, model_name, manufacturer, nominal_capacity, losses_ratio)
    self._type_energy_stored = type_energy_stored
    self._storage_type = storage_type
    self._volume = volume
    self._height = height
    self._layers = layers
    self._maximum_operating_temperature = maximum_operating_temperature
    self._storage_medium = storage_medium
    self._heating_coil_capacity = heating_coil_capacity

  @property
  def type_energy_stored(self):
    """
    Get type of energy stored from ['electrical', 'thermal']
    :return: string
    """
    return self._type_energy_stored

  @property
  def storage_type(self):
    """
    Get storage type from ['thermal', 'sensible', 'latent']
    :return: string
    """
    return self._storage_type

  @property
  def volume(self):
    """
    Get the physical volume of the storage system in cubic meters
    :return: float
    """
    return self._volume

  @property
  def height(self):
    """
    Get the diameter of the storage system in meters
    :return: float
    """
    return self._height

  @property
  def layers(self) -> [Layer]:
    """
    Get construction layers
    :return: [layer]
    """
    return self._layers

  @property
  def maximum_operating_temperature(self):
    """
    Get maximum operating temperature of the storage system in degree Celsius
    :return: float
    """
    return self._maximum_operating_temperature

  @property
  def storage_medium(self) -> Material:
    """
    Get thermodynamic characteristics of the storage medium
    :return: [material
    """
    return self._storage_medium

  @property
  def heating_coil_capacity(self):
    """
    Get heating coil capacity in Watts
    :return: [material
    """
    return self._heating_coil_capacity

  def to_dictionary(self):
    """Class content to dictionary"""
    _layers = None
    _medias = None
    if self.layers is not None:
      _layers = []
      for _layer in self.layers:
        _layers.append(_layer.to_dictionary())

    if self.storage_medium is not None:
      _medias = self.storage_medium.to_dictionary()

    content = {
      'Storage component':
      {
        'storage id': self.id,
        'type of energy stored': self.type_energy_stored,
        'model name': self.model_name,
        'manufacturer': self.manufacturer,
        'storage type': self.storage_type,
        'nominal capacity [J]': self.nominal_capacity,
        'losses-ratio [J/J]': self.losses_ratio,
        'volume [m3]': self.volume,
        'height [m]': self.height,
        'layers': _layers,
        'maximum operating temperature [Celsius]': self.maximum_operating_temperature,
        'storage_medium': _medias,
        'heating coil capacity [W]': self.heating_coil_capacity
      }
    }
    return content
