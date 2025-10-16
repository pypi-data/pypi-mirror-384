import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfShading(IdfBase):
  @staticmethod
  def add(cerc_idf, building):
    name = building.name
    file = cerc_idf.files['shading']
    for s, surface in enumerate(building.surfaces):

      cerc_idf.write_to_idf_format(file, idf_cte.SHADING)
      cerc_idf.write_to_idf_format(file, f'{name}_{s}', 'Name')
      cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Transmittance Schedule Name')
      cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'Number of Vertices')
      eol = ','
      coordinates = cerc_idf.matrix_to_list(surface.solid_polygon.coordinates, cerc_idf.city.lower_corner)
      coordinates_length = len(coordinates)
      for i, coordinate in enumerate(coordinates):
        vertex = i + 1
        if vertex == coordinates_length:
          eol = ';'
        cerc_idf.write_to_idf_format(file, coordinate[0], f'Vertex {vertex} Xcoordinate')
        cerc_idf.write_to_idf_format(file, coordinate[1], f'Vertex {vertex} Ycoordinate')
        cerc_idf.write_to_idf_format(file, coordinate[2], f'Vertex {vertex} Zcoordinate', eol)
