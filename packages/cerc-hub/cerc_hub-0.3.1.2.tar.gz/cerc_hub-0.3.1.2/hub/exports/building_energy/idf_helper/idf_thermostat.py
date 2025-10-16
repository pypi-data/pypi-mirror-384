import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfThermostat(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone):
    thermostat_name = f'Thermostat {thermal_zone.usage_name}'
    heating_schedule = f'Heating thermostat schedules {thermal_zone.usage_name}'
    heating_schedule = cerc_idf.schedules_added_to_idf[heating_schedule]
    cooling_schedule = f'Cooling thermostat schedules {thermal_zone.usage_name}'
    cooling_schedule = cerc_idf.schedules_added_to_idf[cooling_schedule]
    if thermostat_name not in cerc_idf.thermostat_added_to_idf:
      cerc_idf.thermostat_added_to_idf[thermostat_name] = True
      file = cerc_idf.files['thermostat']
      cerc_idf.write_to_idf_format(file, idf_cte.THERMOSTAT)
      cerc_idf.write_to_idf_format(file, thermostat_name, 'Name')
      cerc_idf.write_to_idf_format(file, heating_schedule, 'Heating Setpoint Schedule Name')
      cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Constant Heating Setpoint')
      cerc_idf.write_to_idf_format(file, cooling_schedule, 'Cooling Setpoint Schedule Name', ';')
