"""
Gather and organizes several results for results factories
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
Project Coder Connor Brackley connor.brackley@concordia.ca
"""

class ResultsHandler:
  """
  Gather and organize results
  """

  _building_properties = ['name',
                          'max_height',
                          'function',
                          'year_of_construction',
                          'storeys_above_ground',
                          'floor_area',
                          'energy_systems_archetype_name',
                          'aliases']

  _building_energy_results = ['cooling_peak_load',
                              'heating_peak_load',
                              'lighting_peak_load',
                              'appliances_peak_load',
                              'cooling_demand',
                              'heating_demand',
                              'lighting_electrical_demand',
                              'appliances_electrical_demand',
                              'domestic_hot_water_heat_demand',
                              'heating_consumption',
                              'cooling_consumption',
                              'domestic_hot_water_consumption']

  _building_co2_analysis = ['embodied_co2',
                            'end_of_life_co2']

  @staticmethod
  def collect_results(buildings: list):
    """
    Collects information about each building, energy simulation results, and co2 emissions analysis results.
    Returns a list of all values that were collected and a dictionary containing the values by building.
    :param buildings: list of buildings
    :return: list, dict
    """
    field_names = ['name',
                   'height',
                   'function',
                   'year_of_construction',
                   'number_of_storeys',
                   'footprint_area',
                   'total_area',
                   'energy_system_archetype',
                   'aliases']
    results = []
    for building in buildings:
      name = building.name
      height = building.max_height
      function = building.function
      year_of_construction = building.year_of_construction
      number_of_storeys = building.storeys_above_ground
      footprint_area = building.floor_area
      total_area = building.total_floor_area
      energy_system = building.energy_systems_archetype_name
      aliases = building.aliases

      properties = {'name': name,
                    'height': height,
                    'function': function,
                    'year_of_construction': year_of_construction,
                    'number_of_storeys': number_of_storeys,
                    'footprint_area': footprint_area,
                    'total_area': total_area,
                    'energy_system_archetype': energy_system,
                    'aliases': aliases}

      for energy_result in ResultsHandler._building_energy_results:
        result = getattr(building, energy_result)
        if result:
          for key, energy_values in result.items():
            field_name = f'{key}_{energy_result}'
            if field_name not in field_names:
              field_names.append(field_name)
            properties[field_name] = energy_values

      for co2_emission in ResultsHandler._building_co2_analysis:
        result = getattr(building, co2_emission)
        if result:
          for key, co2_emission_value in result.items():
            field_name = f'{key}_{co2_emission}'
            if field_name not in field_names:
              field_names.append(field_name)
            properties[field_name] = co2_emission_value

      results.append(properties)
    return field_names, results
