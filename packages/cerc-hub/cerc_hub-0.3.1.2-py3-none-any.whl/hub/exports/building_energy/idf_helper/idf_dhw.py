"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfDhw(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    peak_flow_rate = thermal_zone.domestic_hot_water.peak_flow * thermal_zone.total_floor_area
    flow_rate_schedule_name = f'DHW_prof schedules {thermal_zone.usage_name}'
    dhw_schedule_name = f'DHW_temp schedules {thermal_zone.usage_name}'
    cold_temp_schedule_name = f'cold_temp schedules {thermal_zone.usage_name}'
    flow_rate_schedule = cerc_idf.schedules_added_to_idf[flow_rate_schedule_name]
    dhw_schedule = cerc_idf.schedules_added_to_idf[dhw_schedule_name]
    cold_temp_schedule = cerc_idf.schedules_added_to_idf[cold_temp_schedule_name]
    file = cerc_idf.files['dhw']
    cerc_idf.write_to_idf_format(file, idf_cte.DHW)
    cerc_idf.write_to_idf_format(file, zone_name, 'Name')
    cerc_idf.write_to_idf_format(file, zone_name, 'EndUse Subcategory')
    cerc_idf.write_to_idf_format(file, peak_flow_rate, 'Peak Flow Rate')
    cerc_idf.write_to_idf_format(file, flow_rate_schedule, 'Flow Rate Fraction Schedule Name')
    cerc_idf.write_to_idf_format(file, dhw_schedule, 'Target Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, dhw_schedule, 'Hot Water Supply Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, cold_temp_schedule, 'Cold Water Supply Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone Name', ';')
