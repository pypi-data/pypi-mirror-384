"""
Cost catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import xmltodict
from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.cost.archetype import Archetype
from hub.catalog_factories.data_models.cost.content import Content
from hub.catalog_factories.data_models.cost.capital_cost import CapitalCost
from hub.catalog_factories.data_models.cost.chapter import Chapter
from hub.catalog_factories.data_models.cost.item_description import ItemDescription
from hub.catalog_factories.data_models.cost.operational_cost import OperationalCost
from hub.catalog_factories.data_models.cost.fuel import Fuel
from hub.catalog_factories.data_models.cost.income import Income


class MontrealCustomCatalog(Catalog):
  """
  Montreal custom catalog class
  """
  def __init__(self, path):
    path = (path / 'montreal_costs.xml').resolve()
    with open(path, 'r', encoding='utf-8') as xml:
      self._archetypes = xmltodict.parse(xml.read(), force_list='archetype')

    # store the full catalog data model in self._content
    self._content = Content(self._load_archetypes())

  @staticmethod
  def _item_with_threesome(entry, item_type):
    _reposition = float(entry[item_type]['reposition']['#text'])
    _reposition_unit = entry[item_type]['reposition']['@cost_unit']
    _investment = float(entry[item_type]['investment_cost']['#text'])
    _investment_unit = entry[item_type]['investment_cost']['@cost_unit']
    _lifetime = float(entry[item_type]['lifetime_equipment']['#text'])
    _item_description = ItemDescription(item_type,
                                        initial_investment=_investment,
                                        initial_investment_unit=_investment_unit,
                                        reposition=_reposition,
                                        reposition_unit=_reposition_unit,
                                        lifetime=_lifetime)
    return _item_description

  @staticmethod
  def _item_with_refurbishment_values(entry, item_type):
    _refurbishment = float(entry[item_type]['refurbishment_cost']['#text'])
    _refurbishment_unit = entry[item_type]['refurbishment_cost']['@cost_unit']
    _item_description = ItemDescription(item_type,
                                        refurbishment=_refurbishment,
                                        refurbishment_unit=_refurbishment_unit)
    return _item_description

  def _get_capital_costs(self, entry):
    general_chapters = []
    shell = entry['B_shell']
    items_list = []
    item_type = 'B10_superstructure'
    item_description = self._item_with_refurbishment_values(shell, item_type)
    items_list.append(item_description)
    for item in shell['B20_envelope']:
      item_type = item
      item_description = self._item_with_refurbishment_values(shell['B20_envelope'], item_type)
      items_list.append(item_description)
    item_type = 'B3010_opaque_roof'
    item_description = self._item_with_refurbishment_values(shell['B30_roofing'], item_type)
    items_list.append(item_description)
    general_chapters.append(Chapter('B_shell', items_list))
    items_list = []
    item_type = 'D301010_photovoltaic_system'
    services = entry['D_services']
    item_description = self._item_with_threesome(services['D30_hvac']['D3010_energy_supply'], item_type)
    items_list.append(item_description)
    item_type_list = ['D3020_heat_generating_systems', 'D3030_cooling_generation_systems', 'D3040_distribution_systems',
                      'D3080_other_hvac_ahu']
    for item_type in item_type_list:
      item_description = self._item_with_threesome(services['D30_hvac'], item_type)
      items_list.append(item_description)
    item_type = 'D5020_lighting_and_branch_wiring'
    item_description = self._item_with_threesome(services['D50_electrical'], item_type)
    items_list.append(item_description)
    general_chapters.append(Chapter('D_services', items_list))
    allowances = entry['Z_allowances_overhead_profit']
    design_allowance = float(allowances['Z10_design_allowance']['#text']) / 100
    overhead_and_profit = float(allowances['Z20_overhead_profit']['#text']) / 100
    _capital_cost = CapitalCost(general_chapters, design_allowance, overhead_and_profit)

    return _capital_cost

  @staticmethod
  def _get_operational_costs(entry):
    fuels = []
    for item in entry['fuels']['fuel']:
      fuel_type = item['@fuel_type']
      fuel_variable = float(item['variable']['#text'])
      fuel_variable_units = item['variable']['@cost_unit']
      fuel_fixed_monthly = None
      fuel_fixed_peak = None
      if fuel_type == 'electricity':
        fuel_fixed_monthly = float(item['fixed_monthly']['#text'])
        fuel_fixed_peak = float(item['fixed_power']['#text']) / 1000
      elif fuel_type == 'gas':
        fuel_fixed_monthly = float(item['fixed_monthly']['#text'])
      fuel = Fuel(fuel_type,
                  fixed_monthly=fuel_fixed_monthly,
                  fixed_power=fuel_fixed_peak,
                  variable=fuel_variable,
                  variable_units=fuel_variable_units)
      fuels.append(fuel)
    heating_equipment_maintenance = float(entry['maintenance']['heating_equipment']['#text']) / 1000
    cooling_equipment_maintenance = float(entry['maintenance']['cooling_equipment']['#text']) / 1000
    photovoltaic_system_maintenance = float(entry['maintenance']['photovoltaic_system']['#text'])
    co2_emissions = float(entry['co2_cost']['#text'])
    _operational_cost = OperationalCost(fuels,
                                        heating_equipment_maintenance,
                                        cooling_equipment_maintenance,
                                        photovoltaic_system_maintenance,
                                        co2_emissions)
    return _operational_cost

  def _load_archetypes(self):
    _catalog_archetypes = []
    archetypes = self._archetypes['archetypes']['archetype']
    for archetype in archetypes:
      function = archetype['@function']
      municipality = archetype['@municipality']
      country = archetype['@country']
      lod = float(archetype['@lod'])
      currency = archetype['currency']
      capital_cost = self._get_capital_costs(archetype['capital_cost'])
      operational_cost = self._get_operational_costs(archetype['operational_cost'])
      end_of_life_cost = float(archetype['end_of_life_cost']['#text'])
      construction = float(archetype['incomes']['subsidies']['construction']['#text'])
      hvac = float(archetype['incomes']['subsidies']['hvac']['#text'])
      photovoltaic_system = float(archetype['incomes']['subsidies']['photovoltaic']['#text'])
      electricity_exports = float(archetype['incomes']['electricity_export']['#text']) / 1000 / 3600
      reduction_tax = float(archetype['incomes']['tax_reduction']['#text']) / 100
      income = Income(construction_subsidy=construction,
                      hvac_subsidy=hvac,
                      photovoltaic_subsidy=photovoltaic_system,
                      electricity_export=electricity_exports,
                      reductions_tax=reduction_tax)
      _catalog_archetypes.append(Archetype(lod,
                                           function,
                                           municipality,
                                           country,
                                           currency,
                                           capital_cost,
                                           operational_cost,
                                           end_of_life_cost,
                                           income))
    return _catalog_archetypes

  def names(self, category=None):
    """
    Get the catalog elements names
    :parm: for costs catalog category filter does nothing as there is only one category (archetypes)
    """
    _names = {'archetypes': []}
    for archetype in self._content.archetypes:
      _names['archetypes'].append(archetype.name)
    return _names

  def entries(self, category=None):
    """
    Get the catalog elements
    :parm: for costs catalog category filter does nothing as there is only one category (archetypes)
    """
    return self._content

  def get_entry(self, name):
    """
    Get one catalog element by names
    :parm: entry name
    """
    for entry in self._content.archetypes:
      if entry.name.lower() == name.lower():
        return entry
    raise IndexError(f"{name} doesn't exists in the catalog")
