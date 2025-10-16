"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import hub.exports.building_energy.idf_helper as idf_cte
import hub.helpers.constants as cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfInfiltration(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    IdfInfiltration._add_infiltration(cerc_idf, thermal_zone, zone_name, 'AirChanges/Hour', cte.HOUR_TO_SECONDS)

  @staticmethod
  def add_surface(cerc_idf, thermal_zone, zone_name):
    IdfInfiltration._add_infiltration(cerc_idf, thermal_zone, zone_name, 'Flow/ExteriorWallArea', cte.INFILTRATION_75PA_TO_4PA)

  @staticmethod
  def _add_infiltration(cerc_idf, thermal_zone, zone_name, calculation_method, multiplier):
    schedule_name = f'Infiltration schedules {thermal_zone.usage_name}'
    schedule_name = cerc_idf.schedules_added_to_idf[schedule_name]
    infiltration_total = thermal_zone.infiltration_rate_system_off * multiplier
    infiltration_surface = thermal_zone.infiltration_rate_area_system_off * multiplier
    file = cerc_idf.files['infiltration']
    cerc_idf.write_to_idf_format(file, idf_cte.INFILTRATION)
    cerc_idf.write_to_idf_format(file, zone_name, 'Name')
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone or ZoneList or Space or SpaceList Name')
    cerc_idf.write_to_idf_format(file, schedule_name, 'Schedule Name')
    cerc_idf.write_to_idf_format(file, calculation_method, 'Design Flow Rate Calculation Method')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Design Flow Rate')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Flow Rate per Floor Area')
    if calculation_method == 'AirChanges/Hour':
      cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Flow Rate per Exterior Surface Area')
      cerc_idf.write_to_idf_format(file, infiltration_total, 'Air Changes per Hour')
    else:
      cerc_idf.write_to_idf_format(file, infiltration_surface, 'Flow Rate per Exterior Surface Area')
      cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Air Changes per Hour')
    cerc_idf.write_to_idf_format(file, 1, 'Constant Term Coefficient')
    cerc_idf.write_to_idf_format(file, 0, 'Temperature Term Coefficient')
    cerc_idf.write_to_idf_format(file, 0, 'Velocity Term Coefficient')
    cerc_idf.write_to_idf_format(file, 0, 'Velocity Squared Term Coefficient', ';')
