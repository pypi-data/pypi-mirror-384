"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import hub.exports.building_energy.idf_helper as idf_cte
from hub.city_model_structure.building_demand.layer import Layer
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfConstruction(IdfBase):

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
  def _add_default_material(cerc_idf):
    layer = Layer()
    layer.material_name = 'DefaultMaterial'
    layer.thickness = 0.1
    layer.conductivity = 0.1
    layer.density = 1000
    layer.specific_heat = 1000
    layer.thermal_absorptance = 0.9
    layer.solar_absorptance = 0.9
    layer.visible_absorptance = 0.7
    IdfConstruction._add_solid_material(cerc_idf, layer)
    return layer

  @staticmethod
  def add(cerc_idf, thermal_boundary):
    if thermal_boundary.layers is None:
      thermal_boundary.layers = [IdfConstruction._add_default_material(cerc_idf)]
    name = f'{thermal_boundary.construction_name} {thermal_boundary.parent_surface.type}'

    if name not in cerc_idf.constructions_added_to_idf:
      cerc_idf.constructions_added_to_idf[name] = True
      file = cerc_idf.files['constructions']
      cerc_idf.write_to_idf_format(file, idf_cte.CONSTRUCTION)
      cerc_idf.write_to_idf_format(file, name, 'Name')
      eol = ','
      if len(thermal_boundary.layers) == 1:
        eol = ';'
      cerc_idf.write_to_idf_format(file, thermal_boundary.layers[0].material_name, 'Outside Layer', eol)
      for i in range(1, len(thermal_boundary.layers)):
        comment = f'Layer {i + 1}'
        material_name = thermal_boundary.layers[i].material_name
        if i == len(thermal_boundary.layers) - 1:
          eol = ';'
        cerc_idf.write_to_idf_format(file, material_name, comment, eol)
