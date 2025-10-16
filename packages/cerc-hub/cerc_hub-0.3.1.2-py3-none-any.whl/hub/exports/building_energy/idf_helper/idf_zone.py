import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfZone(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    file = cerc_idf.files['zones']
    cerc_idf.write_to_idf_format(file, idf_cte.ZONE)
    cerc_idf.write_to_idf_format(file, zone_name, 'Name')
    cerc_idf.write_to_idf_format(file, 0, 'Direction of Relative North')
    cerc_idf.write_to_idf_format(file, 0, 'X Origin')
    cerc_idf.write_to_idf_format(file, 0, 'Y Origin')
    cerc_idf.write_to_idf_format(file, 0, 'Z Origin')
    cerc_idf.write_to_idf_format(file, 1, 'Type')
    cerc_idf.write_to_idf_format(file, 1, 'Multiplier')
    cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'Ceiling Height')
    cerc_idf.write_to_idf_format(file, thermal_zone.volume, 'Volume')
    cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'Floor Area')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Zone Inside Convection Algorithm')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Zone Outside Convection Algorithm')
    cerc_idf.write_to_idf_format(file, 'Yes', 'Part of Total Floor Area', ';')
