import hub.exports.building_energy.idf_helper as idf_cte
import hub.helpers.constants as cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfVentilation(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    schedule_name = f'Ventilation schedules {thermal_zone.usage_name}'
    schedule_name = cerc_idf.schedules_added_to_idf[schedule_name]
    air_change = thermal_zone.mechanical_air_change * cte.HOUR_TO_SECONDS
    file = cerc_idf.files['ventilation']
    cerc_idf.write_to_idf_format(file, idf_cte.VENTILATION)
    cerc_idf.write_to_idf_format(file, f'{zone_name}_ventilation', 'Name')
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone or ZoneList or Space or SpaceList Name')
    cerc_idf.write_to_idf_format(file, schedule_name, 'Schedule Name')
    cerc_idf.write_to_idf_format(file, 'AirChanges/Hour', 'Design Flow Rate Calculation Method')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Design Flow Rate')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Flow Rate per Floor Area')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Flow Rate per Person')
    cerc_idf.write_to_idf_format(file, air_change, 'Air Changes per Hour')
    cerc_idf.write_to_idf_format(file, 'Natural', 'Ventilation Type')
    cerc_idf.write_to_idf_format(file, 0, 'Fan Pressure Rise')
    cerc_idf.write_to_idf_format(file, 1, 'Fan Total Efficiency')
    cerc_idf.write_to_idf_format(file, 1, 'Constant Term Coefficient')
    cerc_idf.write_to_idf_format(file, 0, 'Temperature Term Coefficient')
    cerc_idf.write_to_idf_format(file, 0, 'Velocity Term Coefficient')
    cerc_idf.write_to_idf_format(file, 0, 'Velocity Squared Term Coefficient')
    cerc_idf.write_to_idf_format(file, -100, 'Minimum Indoor Temperature')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Minimum Indoor Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, 100, 'Maximum Indoor Temperature')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Maximum Indoor Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, -100, 'Delta Temperature')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Delta Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, -100, 'Minimum Outdoor Temperature')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Minimum Outdoor Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, 100, 'Maximum Outdoor Temperature')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Maximum Outdoor Temperature Schedule Name')
    cerc_idf.write_to_idf_format(file, 40, 'Maximum Wind Speed', ';')
