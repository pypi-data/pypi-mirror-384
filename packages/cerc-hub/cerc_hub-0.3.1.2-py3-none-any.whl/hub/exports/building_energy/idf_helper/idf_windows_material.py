import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfWindowsMaterial(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_boundary, thermal_opening):
    name = f'{thermal_boundary.construction_name}_window'
    if name not in cerc_idf.windows_added_to_idf:
      cerc_idf.windows_added_to_idf[name] = True
      file = cerc_idf.files['window_materials']
      cerc_idf.write_to_idf_format(file, idf_cte.WINDOW_MATERIAL)
      cerc_idf.write_to_idf_format(file, name, 'Name')
      cerc_idf.write_to_idf_format(file, thermal_opening.overall_u_value, 'UFactor')
      cerc_idf.write_to_idf_format(file, thermal_opening.g_value, 'Solar Heat Gain Coefficient', ';')
