"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfHeatingSystem(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    schedule_name = f'HVAC AVAIL schedules {thermal_zone.usage_name}'
    availability_schedule = cerc_idf.schedules_added_to_idf[schedule_name]
    thermostat_name = f'Thermostat {thermal_zone.usage_name}'
    file = cerc_idf.files['ideal_load_system']
    cerc_idf.write_to_idf_format(file, idf_cte.IDEAL_LOAD_SYSTEM)
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone Name')
    cerc_idf.write_to_idf_format(file, thermostat_name, 'Template Thermostat Name')
    cerc_idf.write_to_idf_format(file, availability_schedule, 'System Availability Schedule Name')
    cerc_idf.write_to_idf_format(file, 50, 'Maximum Heating Supply Air Temperature')
    cerc_idf.write_to_idf_format(file, 13, 'Minimum Cooling Supply Air Temperature')
    cerc_idf.write_to_idf_format(file, 0.0156, 'Maximum Heating Supply Air Humidity Ratio')
    cerc_idf.write_to_idf_format(file, 0.0077, 'Minimum Cooling Supply Air Humidity Ratio')
    cerc_idf.write_to_idf_format(file, 'NoLimit', 'Heating Limit')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Maximum Heating Air Flow Rate')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Maximum Sensible Heating Capacity')
    cerc_idf.write_to_idf_format(file, 'NoLimit', 'Cooling Limit')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Maximum Cooling Air Flow Rate')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Maximum Total Cooling Capacity')
    cerc_idf.write_to_idf_format(file, availability_schedule, 'Heating Availability Schedule Name')
    cerc_idf.write_to_idf_format(file, availability_schedule, 'Cooling Availability Schedule Name')
    cerc_idf.write_to_idf_format(file, 'ConstantSensibleHeatRatio', 'Dehumidification Control Type')
    cerc_idf.write_to_idf_format(file, 0.7, 'Cooling Sensible Heat Ratio')
    cerc_idf.write_to_idf_format(file, 60, 'Dehumidification Setpoint')
    cerc_idf.write_to_idf_format(file, 'None', 'Humidification Control Type')
    cerc_idf.write_to_idf_format(file, 30, 'Humidification Setpoint')
    cerc_idf.write_to_idf_format(file, 'None', 'Outdoor Air Method')
    cerc_idf.write_to_idf_format(file, 0.00944, 'Outdoor Air Flow Rate per Person')
    cerc_idf.write_to_idf_format(file, 0.0, 'Outdoor Air Flow Rate per Zone Floor Area')
    cerc_idf.write_to_idf_format(file, 0, 'Outdoor Air Flow Rate per Zone')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Design Specification Outdoor Air Object Name')
    cerc_idf.write_to_idf_format(file, 'None', 'Demand Controlled Ventilation Type')
    cerc_idf.write_to_idf_format(file, 'NoEconomizer', 'Outdoor Air Economizer Type')
    cerc_idf.write_to_idf_format(file, 'None', 'Heat Recovery Type')
    cerc_idf.write_to_idf_format(file, 0.70, 'Sensible Heat Recovery Effectiveness')
    cerc_idf.write_to_idf_format(file, 0.65, 'Latent Heat Recovery Effectiveness', ';')
