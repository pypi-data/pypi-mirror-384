import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfLighting(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    storeys_number = int(thermal_zone.total_floor_area / thermal_zone.footprint_area)
    watts_per_zone_floor_area = thermal_zone.lighting.density * storeys_number
    subcategory = f'ELECTRIC EQUIPMENT#{zone_name}#GeneralLights'
    schedule_name = f'Lighting schedules {thermal_zone.usage_name}'
    schedule_name = cerc_idf.schedules_added_to_idf[schedule_name]
    file = cerc_idf.files['lighting']
    cerc_idf.write_to_idf_format(file, idf_cte.LIGHTS)
    cerc_idf.write_to_idf_format(file, f'{zone_name}_lights', 'Name')
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone or ZoneList or Space or SpaceList Name')
    cerc_idf.write_to_idf_format(file, schedule_name, 'Schedule Name')
    cerc_idf.write_to_idf_format(file, 'Watts/Area', 'Design Level Calculation Method')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Lighting Level')
    cerc_idf.write_to_idf_format(file, watts_per_zone_floor_area, 'Watts per Zone Floor Area')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Watts per Person')
    cerc_idf.write_to_idf_format(file, 0, 'Return Air Fraction')
    cerc_idf.write_to_idf_format(file, thermal_zone.lighting.radiative_fraction, 'Fraction Radiant')
    cerc_idf.write_to_idf_format(file, 0, 'Fraction Visible')
    cerc_idf.write_to_idf_format(file, 1, 'Fraction Replaceable')
    cerc_idf.write_to_idf_format(file, subcategory, 'EndUse Subcategory')
    cerc_idf.write_to_idf_format(file, 'No', 'Return Air Fraction Calculated from Plenum Temperature')
    cerc_idf.write_to_idf_format(file, 0, 'Return Air Fraction Function of Plenum Temperature Coefficient 1')
    cerc_idf.write_to_idf_format(file, 0, 'Return Air Fraction Function of Plenum Temperature Coefficient 2', ';')
