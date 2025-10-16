"""
Montreal future system importer
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca

"""

import logging
import copy

from hub.catalog_factories.energy_systems_catalog_factory import EnergySystemsCatalogFactory
from hub.city_model_structure.energy_systems.energy_system import EnergySystem
from hub.city_model_structure.energy_systems.distribution_system import DistributionSystem
from hub.city_model_structure.energy_systems.non_pv_generation_system import NonPvGenerationSystem
from hub.city_model_structure.energy_systems.pv_generation_system import PvGenerationSystem
from hub.city_model_structure.energy_systems.electrical_storage_system import ElectricalStorageSystem
from hub.city_model_structure.energy_systems.thermal_storage_system import ThermalStorageSystem
from hub.city_model_structure.energy_systems.emission_system import EmissionSystem
from hub.helpers.dictionaries import Dictionaries


class MontrealFutureEnergySystemParameters:
  """
  MontrealCustomEnergySystemParameters class
  """

  def __init__(self, city):
    self._city = city

  def enrich_buildings(self):
    """
    Returns the city with the system parameters assigned to the buildings
    :return:
    """
    city = self._city
    montreal_custom_catalog = EnergySystemsCatalogFactory('montreal_future').catalog
    if city.generic_energy_systems is None:
      _generic_energy_systems = {}
    else:
      _generic_energy_systems = city.generic_energy_systems
    for building in city.buildings:
      archetype_name = building.energy_systems_archetype_name
      try:
        archetype = self._search_archetypes(montreal_custom_catalog, archetype_name)
        building.energy_systems_archetype_cluster_id = archetype.cluster_id
      except KeyError:
        logging.error('Building %s has unknown energy system archetype for system name %s', building.name,
                      archetype_name)
        continue

      if archetype.name not in _generic_energy_systems:
        _generic_energy_systems = self._create_generic_systems_list(archetype, _generic_energy_systems)

    city.generic_energy_systems = _generic_energy_systems

    self._assign_energy_systems_to_buildings(city)

  @staticmethod
  def _search_archetypes(catalog, name):
    archetypes = catalog.entries('archetypes')
    for building_archetype in archetypes:
      if str(name) == str(building_archetype.name):
        return building_archetype
    raise KeyError('archetype not found')

  def _create_generic_systems_list(self, archetype, _generic_energy_systems):
    building_systems = []
    for archetype_system in archetype.systems:
      energy_system = EnergySystem()
      _hub_demand_types = []
      for demand_type in archetype_system.demand_types:
        _hub_demand_types.append(Dictionaries().montreal_demand_type_to_hub_energy_demand_type[demand_type])
      energy_system.name = archetype_system.name
      energy_system.demand_types = _hub_demand_types
      energy_system.configuration_schema = archetype_system.configuration_schema
      energy_system.generation_systems = self._create_generation_systems(archetype_system)
      if energy_system.distribution_systems is not None:
        energy_system.distribution_systems = self._create_distribution_systems(archetype_system)
      building_systems.append(energy_system)

    _generic_energy_systems[archetype.name] = building_systems

    return _generic_energy_systems

  def _create_generation_systems(self, archetype_system):
    _generation_systems = []
    archetype_generation_systems = archetype_system.generation_systems
    if archetype_generation_systems is not None:
      for archetype_generation_system in archetype_system.generation_systems:
        if archetype_generation_system.system_type == 'photovoltaic':
          _generation_system = PvGenerationSystem()
          _generation_system.name = archetype_generation_system.name
          _generation_system.model_name = archetype_generation_system.model_name
          _generation_system.manufacturer = archetype_generation_system.manufacturer
          _type = archetype_generation_system.system_type
          _generation_system.system_type = Dictionaries().montreal_generation_system_to_hub_energy_generation_system[_type]
          _fuel_type = Dictionaries().montreal_custom_fuel_to_hub_fuel[archetype_generation_system.fuel_type]
          _generation_system.fuel_type = _fuel_type
          _generation_system.electricity_efficiency = archetype_generation_system.electricity_efficiency
          _generation_system.nominal_electricity_output = archetype_generation_system.nominal_electricity_output
          _generation_system.nominal_ambient_temperature = archetype_generation_system.nominal_ambient_temperature
          _generation_system.nominal_cell_temperature = archetype_generation_system.nominal_cell_temperature
          _generation_system.nominal_radiation = archetype_generation_system.nominal_radiation
          _generation_system.standard_test_condition_cell_temperature = archetype_generation_system.standard_test_condition_cell_temperature
          _generation_system.standard_test_condition_maximum_power = archetype_generation_system.standard_test_condition_maximum_power
          _generation_system.standard_test_condition_radiation = archetype_generation_system.standard_test_condition_radiation
          _generation_system.cell_temperature_coefficient = archetype_generation_system.cell_temperature_coefficient
          _generation_system.width = archetype_generation_system.width
          _generation_system.height = archetype_generation_system.height
          _generation_system.tilt_angle = self._city.latitude
          _generic_storage_system = None
          if archetype_generation_system.energy_storage_systems is not None:
            _storage_systems = []
            for storage_system in archetype_generation_system.energy_storage_systems:
              if storage_system.type_energy_stored == 'electrical':
                _generic_storage_system = ElectricalStorageSystem()
                _generic_storage_system.type_energy_stored = 'electrical'
              _storage_systems.append(_generic_storage_system)
            _generation_system.energy_storage_systems = _storage_systems

        else:
          _generation_system = NonPvGenerationSystem()
          _generation_system.name = archetype_generation_system.name
          _generation_system.model_name = archetype_generation_system.model_name
          _generation_system.manufacturer = archetype_generation_system.manufacturer
          _type = archetype_generation_system.system_type
          _generation_system.system_type = Dictionaries().montreal_generation_system_to_hub_energy_generation_system[_type]
          _fuel_type = Dictionaries().montreal_custom_fuel_to_hub_fuel[archetype_generation_system.fuel_type]
          _generation_system.fuel_type = _fuel_type
          _generation_system.nominal_heat_output = archetype_generation_system.nominal_heat_output
          _generation_system.nominal_cooling_output = archetype_generation_system.nominal_cooling_output
          _generation_system.maximum_heat_output = archetype_generation_system.maximum_heat_output
          _generation_system.minimum_heat_output = archetype_generation_system.minimum_heat_output
          _generation_system.maximum_cooling_output = archetype_generation_system.maximum_cooling_output
          _generation_system.minimum_cooling_output = archetype_generation_system.minimum_cooling_output
          _generation_system.source_temperature = archetype_generation_system.source_temperature
          _generation_system.source_mass_flow = archetype_generation_system.source_mass_flow
          _generation_system.supply_medium = archetype_generation_system.supply_medium
          _generation_system.maximum_heat_supply_temperature = archetype_generation_system.maximum_heat_supply_temperature
          _generation_system.maximum_cooling_supply_temperature = archetype_generation_system.maximum_cooling_supply_temperature
          _generation_system.minimum_heat_supply_temperature = archetype_generation_system.minimum_heat_supply_temperature
          _generation_system.minimum_cooling_supply_temperature = archetype_generation_system.minimum_cooling_supply_temperature
          _generation_system.heat_output_curve = archetype_generation_system.heat_output_curve
          _generation_system.heat_fuel_consumption_curve = archetype_generation_system.heat_fuel_consumption_curve
          _generation_system.heat_efficiency_curve = archetype_generation_system.heat_efficiency_curve
          _generation_system.cooling_output_curve = archetype_generation_system.cooling_output_curve
          _generation_system.cooling_fuel_consumption_curve = archetype_generation_system.cooling_fuel_consumption_curve
          _generation_system.cooling_efficiency_curve = archetype_generation_system.cooling_efficiency_curve
          _generation_system.domestic_hot_water = archetype_generation_system.domestic_hot_water
          _generation_system.nominal_electricity_output = archetype_generation_system.nominal_electricity_output
          _generation_system.source_medium = archetype_generation_system.source_medium
          _generation_system.heat_efficiency = archetype_generation_system.heat_efficiency
          _generation_system.cooling_efficiency = archetype_generation_system.cooling_efficiency
          _generation_system.electricity_efficiency = archetype_generation_system.electricity_efficiency
          _generation_system.reversibility = archetype_generation_system.reversibility
          _generic_storage_system = None
          if archetype_generation_system.energy_storage_systems is not None:
            _storage_systems = []
            for storage_system in archetype_generation_system.energy_storage_systems:
              if storage_system.type_energy_stored == 'electrical':
                _generic_storage_system = ElectricalStorageSystem()
                _generic_storage_system.type_energy_stored = 'electrical'
              else:
                _generic_storage_system = ThermalStorageSystem()
                _generic_storage_system.type_energy_stored = storage_system.type_energy_stored
                _generic_storage_system.height = storage_system.height
                _generic_storage_system.layers = storage_system.layers
                _generic_storage_system.storage_medium = storage_system.storage_medium
                _generic_storage_system.heating_coil_capacity = storage_system.heating_coil_capacity
              _storage_systems.append(_generic_storage_system)
            _generation_system.energy_storage_systems = _storage_systems
          if archetype_generation_system.domestic_hot_water:
            _generation_system.domestic_hot_water = True
          if archetype_generation_system.reversibility:
            _generation_system.reversibility = True
          if archetype_generation_system.simultaneous_heat_cold:
            _generation_system.simultaneous_heat_cold = True
        _generation_systems.append(_generation_system)
    return _generation_systems

  @staticmethod
  def _create_distribution_systems(archetype_system):
    _distribution_systems = []
    archetype_distribution_systems = archetype_system.distribution_systems
    if archetype_distribution_systems is not None:
      for archetype_distribution_system in archetype_system.distribution_systems:
        _distribution_system = DistributionSystem()
        _distribution_system.type = archetype_distribution_system.type
        _distribution_system.distribution_consumption_fix_flow = \
          archetype_distribution_system.distribution_consumption_fix_flow
        _distribution_system.distribution_consumption_variable_flow = \
          archetype_distribution_system.distribution_consumption_variable_flow
        _distribution_system.heat_losses = archetype_distribution_system.heat_losses
        _generic_emission_system = None
        if archetype_distribution_system.emission_systems is not None:
          _emission_systems = []
          for emission_system in archetype_distribution_system.emission_systems:
            _generic_emission_system = EmissionSystem()
            _generic_emission_system.parasitic_energy_consumption = emission_system.parasitic_energy_consumption
            _emission_systems.append(_generic_emission_system)
          _distribution_system.emission_systems = _emission_systems
        _distribution_systems.append(_distribution_system)
      return _distribution_systems

  @staticmethod
  def _assign_energy_systems_to_buildings(city):
    for building in city.buildings:
      _building_energy_systems = []
      energy_systems_cluster_name = building.energy_systems_archetype_name
      if str(energy_systems_cluster_name) == 'nan':
        break
      _generic_building_energy_systems = city.generic_energy_systems[energy_systems_cluster_name]
      for _generic_building_energy_system in _generic_building_energy_systems:
        _building_energy_systems.append(copy.deepcopy(_generic_building_energy_system))

      building.energy_systems = _building_energy_systems
