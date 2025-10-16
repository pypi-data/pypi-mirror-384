"""
Energy System catalog electrical storage system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

from hub.catalog_factories.data_models.energy_systems.energy_storage_system import EnergyStorageSystem


class ElectricalStorageSystem(EnergyStorageSystem):
  """"
  Energy Storage System Class
  """

  def __init__(self, storage_id, type_energy_stored=None, model_name=None, manufacturer=None, storage_type=None,
               nominal_capacity=None, losses_ratio=None, rated_output_power=None, nominal_efficiency=None,
               battery_voltage=None, depth_of_discharge=None, self_discharge_rate=None):

    super().__init__(storage_id, model_name, manufacturer, nominal_capacity, losses_ratio)
    self._type_energy_stored = type_energy_stored
    self._storage_type = storage_type
    self._rated_output_power = rated_output_power
    self._nominal_efficiency = nominal_efficiency
    self._battery_voltage = battery_voltage
    self._depth_of_discharge = depth_of_discharge
    self._self_discharge_rate = self_discharge_rate

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
    Get storage type from ['lithium_ion', 'lead_acid', 'NiCd']
    :return: string
    """
    return self._storage_type

  @property
  def rated_output_power(self):
    """
    Get the rated output power of storage system in Watts
    :return: float
    """
    return self._rated_output_power

  @property
  def nominal_efficiency(self):
    """
     Get the nominal efficiency of the storage system
    :return: float
    """
    return self._nominal_efficiency

  @property
  def battery_voltage(self):
    """
    Get the battery voltage in Volts
    :return: float
    """
    return self._battery_voltage

  @property
  def depth_of_discharge(self):
    """
    Get the depth of discharge as a percentage
    :return: float
    """
    return self._depth_of_discharge

  @property
  def self_discharge_rate(self):
    """
    Get the self discharge rate of battery as a percentage
    :return: float
    """
    return self._self_discharge_rate

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Storage component': {
      'storage id': self.id,
      'type of energy stored': self.type_energy_stored,
      'model name': self.model_name,
      'manufacturer': self.manufacturer,
      'storage type': self.storage_type,
      'nominal capacity [J]': self.nominal_capacity,
      'losses-ratio [J/J]': self.losses_ratio,
      'rated power [W]': self.rated_output_power,
      'nominal efficiency': self.nominal_efficiency,
      'battery voltage [V]': self.battery_voltage,
      'depth of discharge [%]': self.depth_of_discharge,
      'self discharge rate': self.self_discharge_rate
    }
    }
    return content
