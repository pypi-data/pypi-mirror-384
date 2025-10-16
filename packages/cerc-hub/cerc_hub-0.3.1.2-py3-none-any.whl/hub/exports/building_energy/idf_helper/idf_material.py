import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfMaterial(IdfBase):
  @staticmethod
  def _add_solid_material(cerc_idf, layer):
    file = cerc_idf.files['solid_materials']
    cerc_idf.write_to_idf_format(file, idf_cte.SOLID_MATERIAL)
    cerc_idf.write_to_idf_format(file, layer.material_name, 'Name')
    cerc_idf.write_to_idf_format(file, idf_cte.ROUGHNESS, 'Roughness')
    cerc_idf.write_to_idf_format(file, layer.thickness, 'Thickness')
    cerc_idf.write_to_idf_format(file, layer.conductivity, 'Conductivity')
    cerc_idf.write_to_idf_format(file, layer.density, 'Density')
    cerc_idf.write_to_idf_format(file, layer.specific_heat, 'Specific Heat')
    cerc_idf.write_to_idf_format(file, layer.thermal_absorptance, 'Thermal Absorptance')
    cerc_idf.write_to_idf_format(file, layer.solar_absorptance, 'Solar Absorptance')
    cerc_idf.write_to_idf_format(file, layer.visible_absorptance, 'Visible Absorptance', ';')

  @staticmethod
  def _add_nomass_material(cerc_idf, layer):
    file = cerc_idf.files['nomass_materials']
    cerc_idf.write_to_idf_format(file, idf_cte.NOMASS_MATERIAL)
    cerc_idf.write_to_idf_format(file, layer.material_name, 'Name')
    cerc_idf.write_to_idf_format(file, idf_cte.ROUGHNESS, 'Roughness')
    cerc_idf.write_to_idf_format(file, layer.thermal_resistance, 'Thermal Resistance')
    cerc_idf.write_to_idf_format(file, 0.9, 'Thermal Absorptance')
    cerc_idf.write_to_idf_format(file, 0.7, 'Solar Absorptance')
    cerc_idf.write_to_idf_format(file, 0.7, 'Visible Absorptance', ';')

  @staticmethod
  def add(cerc_idf, thermal_boundary):
    for layer in thermal_boundary.layers:
      if layer.material_name not in cerc_idf.materials_added_to_idf:
        cerc_idf.materials_added_to_idf[layer.material_name] = True
        if layer.no_mass:
          IdfMaterial._add_nomass_material(cerc_idf, layer)
        else:
          IdfMaterial._add_solid_material(cerc_idf, layer)
