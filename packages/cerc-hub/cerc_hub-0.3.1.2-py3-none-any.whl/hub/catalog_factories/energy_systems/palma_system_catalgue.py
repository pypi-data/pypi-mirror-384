"""
Palma energy system catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
"""

import xmltodict
from pathlib import Path
from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.energy_systems.distribution_system import DistributionSystem
from hub.catalog_factories.data_models.energy_systems.emission_system import EmissionSystem
from hub.catalog_factories.data_models.energy_systems.system import System
from hub.catalog_factories.data_models.energy_systems.content import Content
from hub.catalog_factories.data_models.energy_systems.non_pv_generation_system import NonPvGenerationSystem
from hub.catalog_factories.data_models.energy_systems.pv_generation_system import PvGenerationSystem
from hub.catalog_factories.data_models.energy_systems.thermal_storage_system import ThermalStorageSystem
from hub.catalog_factories.data_models.energy_systems.performance_curves import PerformanceCurves
from hub.catalog_factories.data_models.energy_systems.archetype import Archetype
from hub.catalog_factories.data_models.construction.material import Material
from hub.catalog_factories.data_models.construction.layer import Layer


class PalmaSystemCatalogue(Catalog):
  """
  North america energy system catalog class
  """

  def __init__(self, path):
    path = str(path / 'palma_systems.xml')
    with open(path, 'r', encoding='utf-8') as xml:
      self._archetypes = xmltodict.parse(xml.read(),
                                         force_list=['pv_generation_component', 'demand'])

    self._storage_components = self._load_storage_components()
    self._generation_components = self._load_generation_components()
    self._energy_emission_components = self._load_emission_equipments()
    self._distribution_components = self._load_distribution_equipments()
    self._systems = self._load_systems()
    self._system_archetypes = self._load_archetypes()
    self._content = Content(self._system_archetypes,
                            self._systems,
                            generations=self._generation_components,
                            distributions=self._distribution_components)

  def _load_generation_components(self):
    generation_components = []
    non_pv_generation_components = self._archetypes['EnergySystemCatalog']['energy_generation_components'][
      'non_pv_generation_component']
    if non_pv_generation_components is not None:
      for non_pv in non_pv_generation_components:
        system_id = non_pv['system_id']
        name = non_pv['name']
        system_type = non_pv['system_type']
        model_name = non_pv['model_name']
        manufacturer = non_pv['manufacturer']
        fuel_type = non_pv['fuel_type']
        distribution_systems = non_pv['distribution_systems']
        energy_storage_systems = None
        if non_pv['energy_storage_systems'] is not None:
          storage_component = non_pv['energy_storage_systems']['storage_id']
          storage_systems = self._search_storage_equipment(self._load_storage_components(), storage_component)
          energy_storage_systems = storage_systems
        nominal_heat_output = non_pv['nominal_heat_output']
        maximum_heat_output = non_pv['maximum_heat_output']
        minimum_heat_output = non_pv['minimum_heat_output']
        source_medium = non_pv['source_medium']
        supply_medium = non_pv['supply_medium']
        heat_efficiency = non_pv['heat_efficiency']
        nominal_cooling_output = non_pv['nominal_cooling_output']
        maximum_cooling_output = non_pv['maximum_cooling_output']
        minimum_cooling_output = non_pv['minimum_cooling_output']
        cooling_efficiency = non_pv['cooling_efficiency']
        electricity_efficiency = non_pv['electricity_efficiency']
        source_temperature = non_pv['source_temperature']
        source_mass_flow = non_pv['source_mass_flow']
        nominal_electricity_output = non_pv['nominal_electricity_output']
        maximum_heat_supply_temperature = non_pv['maximum_heat_supply_temperature']
        minimum_heat_supply_temperature = non_pv['minimum_heat_supply_temperature']
        maximum_cooling_supply_temperature = non_pv['maximum_cooling_supply_temperature']
        minimum_cooling_supply_temperature = non_pv['minimum_cooling_supply_temperature']
        heat_output_curve = None
        heat_fuel_consumption_curve = None
        heat_efficiency_curve = None
        cooling_output_curve = None
        cooling_fuel_consumption_curve = None
        cooling_efficiency_curve = None
        if non_pv['heat_output_curve'] is not None:
          curve_type = non_pv['heat_output_curve']['curve_type']
          dependant_variable = non_pv['heat_output_curve']['dependant_variable']
          parameters = non_pv['heat_output_curve']['parameters']
          coefficients = list(non_pv['heat_output_curve']['coefficients'].values())
          heat_output_curve = PerformanceCurves(curve_type, dependant_variable, parameters, coefficients)
        if non_pv['heat_fuel_consumption_curve'] is not None:
          curve_type = non_pv['heat_fuel_consumption_curve']['curve_type']
          dependant_variable = non_pv['heat_fuel_consumption_curve']['dependant_variable']
          parameters = non_pv['heat_fuel_consumption_curve']['parameters']
          coefficients = list(non_pv['heat_fuel_consumption_curve']['coefficients'].values())
          heat_fuel_consumption_curve = PerformanceCurves(curve_type, dependant_variable, parameters, coefficients)
        if non_pv['heat_efficiency_curve'] is not None:
          curve_type = non_pv['heat_efficiency_curve']['curve_type']
          dependant_variable = non_pv['heat_efficiency_curve']['dependant_variable']
          parameters = non_pv['heat_efficiency_curve']['parameters']
          coefficients = list(non_pv['heat_efficiency_curve']['coefficients'].values())
          heat_efficiency_curve = PerformanceCurves(curve_type, dependant_variable, parameters, coefficients)
        if non_pv['cooling_output_curve'] is not None:
          curve_type = non_pv['cooling_output_curve']['curve_type']
          dependant_variable = non_pv['cooling_output_curve']['dependant_variable']
          parameters = non_pv['cooling_output_curve']['parameters']
          coefficients = list(non_pv['cooling_output_curve']['coefficients'].values())
          cooling_output_curve = PerformanceCurves(curve_type, dependant_variable, parameters, coefficients)
        if non_pv['cooling_fuel_consumption_curve'] is not None:
          curve_type = non_pv['cooling_fuel_consumption_curve']['curve_type']
          dependant_variable = non_pv['cooling_fuel_consumption_curve']['dependant_variable']
          parameters = non_pv['cooling_fuel_consumption_curve']['parameters']
          coefficients = list(non_pv['cooling_fuel_consumption_curve']['coefficients'].values())
          cooling_fuel_consumption_curve = PerformanceCurves(curve_type, dependant_variable, parameters, coefficients)
        if non_pv['cooling_efficiency_curve'] is not None:
          curve_type = non_pv['cooling_efficiency_curve']['curve_type']
          dependant_variable = non_pv['cooling_efficiency_curve']['dependant_variable']
          parameters = non_pv['cooling_efficiency_curve']['parameters']
          coefficients = list(non_pv['cooling_efficiency_curve']['coefficients'].values())
          cooling_efficiency_curve = PerformanceCurves(curve_type, dependant_variable, parameters, coefficients)
        dhw = None
        if non_pv['domestic_hot_water'] is not None:
          if non_pv['domestic_hot_water'] == 'True':
            dhw = True
          else:
            dhw = False

        reversible = None
        if non_pv['reversible'] is not None:
          if non_pv['reversible'] == 'True':
            reversible = True
          else:
            reversible = False

        dual_supply = None
        if non_pv['simultaneous_heat_cold'] is not None:
          if non_pv['simultaneous_heat_cold'] == 'True':
            dual_supply = True
          else:
            dual_supply = False
        non_pv_component = NonPvGenerationSystem(system_id=system_id,
                                                 name=name,
                                                 system_type=system_type,
                                                 model_name=model_name,
                                                 manufacturer=manufacturer,
                                                 fuel_type=fuel_type,
                                                 nominal_heat_output=nominal_heat_output,
                                                 maximum_heat_output=maximum_heat_output,
                                                 minimum_heat_output=minimum_heat_output,
                                                 source_medium=source_medium,
                                                 supply_medium=supply_medium,
                                                 heat_efficiency=heat_efficiency,
                                                 nominal_cooling_output=nominal_cooling_output,
                                                 maximum_cooling_output=maximum_cooling_output,
                                                 minimum_cooling_output=minimum_cooling_output,
                                                 cooling_efficiency=cooling_efficiency,
                                                 electricity_efficiency=electricity_efficiency,
                                                 source_temperature=source_temperature,
                                                 source_mass_flow=source_mass_flow,
                                                 nominal_electricity_output=nominal_electricity_output,
                                                 maximum_heat_supply_temperature=maximum_heat_supply_temperature,
                                                 minimum_heat_supply_temperature=minimum_heat_supply_temperature,
                                                 maximum_cooling_supply_temperature=maximum_cooling_supply_temperature,
                                                 minimum_cooling_supply_temperature=minimum_cooling_supply_temperature,
                                                 heat_output_curve=heat_output_curve,
                                                 heat_fuel_consumption_curve=heat_fuel_consumption_curve,
                                                 heat_efficiency_curve=heat_efficiency_curve,
                                                 cooling_output_curve=cooling_output_curve,
                                                 cooling_fuel_consumption_curve=cooling_fuel_consumption_curve,
                                                 cooling_efficiency_curve=cooling_efficiency_curve,
                                                 distribution_systems=distribution_systems,
                                                 energy_storage_systems=energy_storage_systems,
                                                 domestic_hot_water=dhw,
                                                 reversible=reversible,
                                                 simultaneous_heat_cold=dual_supply)
        generation_components.append(non_pv_component)
    pv_generation_components = self._archetypes['EnergySystemCatalog']['energy_generation_components'][
      'pv_generation_component']
    if pv_generation_components is not None:
      for pv in pv_generation_components:
        system_id = pv['system_id']
        name = pv['name']
        system_type = pv['system_type']
        model_name = pv['model_name']
        manufacturer = pv['manufacturer']
        electricity_efficiency = pv['electricity_efficiency']
        nominal_electricity_output = pv['nominal_electricity_output']
        nominal_ambient_temperature = pv['nominal_ambient_temperature']
        nominal_cell_temperature = pv['nominal_cell_temperature']
        nominal_radiation = pv['nominal_radiation']
        standard_test_condition_cell_temperature = pv['standard_test_condition_cell_temperature']
        standard_test_condition_maximum_power = pv['standard_test_condition_maximum_power']
        standard_test_condition_radiation = pv['standard_test_condition_radiation']
        cell_temperature_coefficient = pv['cell_temperature_coefficient']
        width = pv['width']
        height = pv['height']
        distribution_systems = pv['distribution_systems']
        energy_storage_systems = None
        if pv['energy_storage_systems'] is not None:
          storage_component = pv['energy_storage_systems']['storage_id']
          storage_systems = self._search_storage_equipment(self._load_storage_components(), storage_component)
          energy_storage_systems = storage_systems
        pv_component = PvGenerationSystem(system_id=system_id,
                                          name=name,
                                          system_type=system_type,
                                          model_name=model_name,
                                          manufacturer=manufacturer,
                                          electricity_efficiency=electricity_efficiency,
                                          nominal_electricity_output=nominal_electricity_output,
                                          nominal_ambient_temperature=nominal_ambient_temperature,
                                          nominal_cell_temperature=nominal_cell_temperature,
                                          nominal_radiation=nominal_radiation,
                                          standard_test_condition_cell_temperature=
                                          standard_test_condition_cell_temperature,
                                          standard_test_condition_maximum_power=standard_test_condition_maximum_power,
                                          standard_test_condition_radiation=standard_test_condition_radiation,
                                          cell_temperature_coefficient=cell_temperature_coefficient,
                                          width=width,
                                          height=height,
                                          distribution_systems=distribution_systems,
                                          energy_storage_systems=energy_storage_systems)
        generation_components.append(pv_component)

    return generation_components

  def _load_distribution_equipments(self):
    _equipments = []
    distribution_systems = self._archetypes['EnergySystemCatalog']['distribution_systems']['distribution_system']
    if distribution_systems is not None:
      for distribution_system in distribution_systems:
        system_id = None
        model_name = None
        system_type = None
        supply_temperature = None
        distribution_consumption_fix_flow = None
        distribution_consumption_variable_flow = None
        heat_losses = None
        generation_systems = None
        energy_storage_systems = None
        emission_systems = None
        distribution_equipment = DistributionSystem(system_id=system_id,
                                                    model_name=model_name,
                                                    system_type=system_type,
                                                    supply_temperature=supply_temperature,
                                                    distribution_consumption_fix_flow=distribution_consumption_fix_flow,
                                                    distribution_consumption_variable_flow=
                                                    distribution_consumption_variable_flow,
                                                    heat_losses=heat_losses,
                                                    generation_systems=generation_systems,
                                                    energy_storage_systems=energy_storage_systems,
                                                    emission_systems=emission_systems
                                                    )
        _equipments.append(distribution_equipment)
    return _equipments

  def _load_emission_equipments(self):
    _equipments = []
    dissipation_systems = self._archetypes['EnergySystemCatalog']['dissipation_systems']['dissipation_system']
    if dissipation_systems is not None:
      for dissipation_system in dissipation_systems:
        system_id = None
        model_name = None
        system_type = None
        parasitic_energy_consumption = 0
        emission_system = EmissionSystem(system_id=system_id,
                                         model_name=model_name,
                                         system_type=system_type,
                                         parasitic_energy_consumption=parasitic_energy_consumption)
        _equipments.append(emission_system)
    return _equipments

  def _load_storage_components(self):
    storage_components = []
    thermal_storages = self._archetypes['EnergySystemCatalog']['energy_storage_components']['thermalStorages']
    for tes in thermal_storages:
      storage_id = tes['storage_id']
      type_energy_stored = tes['type_energy_stored']
      model_name = tes['model_name']
      manufacturer = tes['manufacturer']
      storage_type = tes['storage_type']
      volume = tes['physical_characteristics']['volume']
      height = tes['physical_characteristics']['height']
      maximum_operating_temperature = tes['maximum_operating_temperature']
      materials = self._load_materials()
      insulation_material_id = tes['insulation']['material_id']
      insulation_material = self._search_material(materials, insulation_material_id)
      material_id = tes['physical_characteristics']['material_id']
      tank_material = self._search_material(materials, material_id)
      thickness = float(tes['insulation']['insulationThickness']) / 100  # from cm to m
      insulation_layer = Layer(None, 'insulation', insulation_material, thickness)
      thickness = float(tes['physical_characteristics']['tankThickness']) / 100  # from cm to m
      tank_layer = Layer(None, 'tank', tank_material, thickness)
      media = self._load_media()
      media_id = tes['storage_medium']['medium_id']
      medium = self._search_media(media, media_id)
      layers = [insulation_layer, tank_layer]
      nominal_capacity = tes['nominal_capacity']
      losses_ratio = tes['losses_ratio']
      heating_coil_capacity = tes['heating_coil_capacity']
      storage_component = ThermalStorageSystem(storage_id=storage_id,
                                               model_name=model_name,
                                               type_energy_stored=type_energy_stored,
                                               manufacturer=manufacturer,
                                               storage_type=storage_type,
                                               nominal_capacity=nominal_capacity,
                                               losses_ratio=losses_ratio,
                                               volume=volume,
                                               height=height,
                                               layers=layers,
                                               maximum_operating_temperature=maximum_operating_temperature,
                                               storage_medium=medium,
                                               heating_coil_capacity=heating_coil_capacity)
      storage_components.append(storage_component)
    return storage_components

  def _load_systems(self):
    base_path = Path(Path(__file__).parent.parent.parent / 'data/energy_systems')
    _catalog_systems = []
    systems = self._archetypes['EnergySystemCatalog']['systems']['system']
    for system in systems:
      system_id = system['id']
      name = system['name']
      demands = system['demands']['demand']
      generation_components = system['components']['generation_id']
      generation_systems = self._search_generation_equipment(self._load_generation_components(), generation_components)
      configuration_schema = None
      if system['schema'] is not None:
        configuration_schema = Path(base_path / system['schema'])
      energy_system = System(system_id=system_id,
                             name=name,
                             demand_types=demands,
                             generation_systems=generation_systems,
                             distribution_systems=None,
                             configuration_schema=configuration_schema)
      _catalog_systems.append(energy_system)
    return _catalog_systems

  def _load_archetypes(self):
    _system_archetypes = []
    system_clusters = self._archetypes['EnergySystemCatalog']['system_archetypes']['system_archetype']
    for system_cluster in system_clusters:
      name = system_cluster['name']
      systems = system_cluster['systems']['system_id']
      integer_system_ids = [int(item) for item in systems]
      _systems = []
      for system_archetype in self._systems:
        if int(system_archetype.id) in integer_system_ids:
          _systems.append(system_archetype)
      _system_archetypes.append(Archetype(name=name, systems=_systems))
    return _system_archetypes

  def _load_materials(self):
    materials = []
    _materials = self._archetypes['EnergySystemCatalog']['materials']['material']
    for _material in _materials:
      material_id = _material['material_id']
      name = _material['name']
      conductivity = _material['conductivity']
      solar_absorptance = _material['solar_absorptance']
      thermal_absorptance = _material['thermal_absorptance']
      density = _material['density']
      specific_heat = _material['specific_heat']
      no_mass = _material['no_mass']
      visible_absorptance = _material['visible_absorptance']
      thermal_resistance = _material['thermal_resistance']

      material = Material(material_id,
                          name,
                          solar_absorptance=solar_absorptance,
                          thermal_absorptance=thermal_absorptance,
                          density=density,
                          conductivity=conductivity,
                          thermal_resistance=thermal_resistance,
                          visible_absorptance=visible_absorptance,
                          no_mass=no_mass,
                          specific_heat=specific_heat)
      materials.append(material)
    return materials

  @staticmethod
  def _search_material(materials, material_id):
    _material = None
    for material in materials:
      if int(material.id) == int(material_id):
        _material = material
        break
    if _material is None:
      raise ValueError(f'Material with the id = [{material_id}] not found in catalog ')
    return _material

  def _load_media(self):
    media = []
    _media = [self._archetypes['EnergySystemCatalog']['media']['medium']]
    for _medium in _media:
      medium_id = _medium['medium_id']
      density = _medium['density']
      name = _medium['name']
      conductivity = _medium['conductivity']
      solar_absorptance = _medium['solar_absorptance']
      thermal_absorptance = _medium['thermal_absorptance']
      specific_heat = _medium['specific_heat']
      no_mass = _medium['no_mass']
      visible_absorptance = _medium['visible_absorptance']
      thermal_resistance = _medium['thermal_resistance']
      medium = Material(material_id=medium_id,
                        name=name,
                        solar_absorptance=solar_absorptance,
                        thermal_absorptance=thermal_absorptance,
                        visible_absorptance=visible_absorptance,
                        no_mass=no_mass,
                        thermal_resistance=thermal_resistance,
                        conductivity=conductivity,
                        density=density,
                        specific_heat=specific_heat)
      media.append(medium)
    return media

  @staticmethod
  def _search_media(media, medium_id):
    _medium = None
    for medium in media:
      if int(medium.id) == int(medium_id):
        _medium = medium
        break
    if _medium is None:
      raise ValueError(f'media with the id = [{medium_id}] not found in catalog ')
    return _medium

  @staticmethod
  def _search_generation_equipment(generation_systems, generation_id):
    _generation_systems = []

    if isinstance(generation_id, list):
      integer_ids = [int(item) for item in generation_id]
      for generation in generation_systems:
        if int(generation.id) in integer_ids:
          _generation_systems.append(generation)
    else:
      integer_id = int(generation_id)
      for generation in generation_systems:
        if int(generation.id) == integer_id:
          _generation_systems.append(generation)

    if len(_generation_systems) == 0:
      _generation_systems = None
      raise ValueError(f'The system with the following id is not found in catalog [{generation_id}]')
    return _generation_systems

  @staticmethod
  def _search_storage_equipment(storage_systems, storage_id):
    _storage_systems = []
    for storage in storage_systems:
      if storage.id in storage_id:
        _storage_systems.append(storage)
    if len(_storage_systems) == 0:
      _storage_systems = None
      raise ValueError(f'The system with the following id is not found in catalog [{storage_id}]')
    return _storage_systems

  def names(self, category=None):
    """
    Get the catalog elements names
    :parm: optional category filter
    """
    if category is None:
      _names = {'archetypes': [], 'systems': [], 'generation_equipments': [], 'storage_equipments': []}
      for archetype in self._content.archetypes:
        _names['archetypes'].append(archetype.name)
      for system in self._content.systems:
        _names['systems'].append(system.name)
      for equipment in self._content.generation_equipments:
        _names['generation_equipments'].append(equipment.name)
    else:
      _names = {category: []}
      if category.lower() == 'archetypes':
        for archetype in self._content.archetypes:
          _names[category].append(archetype.name)
      elif category.lower() == 'systems':
        for system in self._content.systems:
          _names[category].append(system.name)
      elif category.lower() == 'generation_equipments':
        for system in self._content.generation_equipments:
          _names[category].append(system.name)
      else:
        raise ValueError(f'Unknown category [{category}]')
    return _names

  def entries(self, category=None):
    """
    Get the catalog elements
    :parm: optional category filter
    """
    if category is None:
      return self._content
    if category.lower() == 'archetypes':
      return self._content.archetypes
    if category.lower() == 'systems':
      return self._content.systems
    if category.lower() == 'generation_equipments':
      return self._content.generation_equipments
    raise ValueError(f'Unknown category [{category}]')

  def get_entry(self, name):
    """
    Get one catalog element by names
    :parm: entry name
    """
    for entry in self._content.archetypes:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.systems:
      if entry.name.lower() == name.lower():
        return entry
    for entry in self._content.generation_equipments:
      if entry.name.lower() == name.lower():
        return entry
    raise IndexError(f"{name} doesn't exists in the catalog")
