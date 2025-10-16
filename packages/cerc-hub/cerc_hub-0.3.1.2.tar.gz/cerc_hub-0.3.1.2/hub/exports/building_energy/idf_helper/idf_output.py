from pathlib import Path

from hub.exports.building_energy.idf_helper.idf_base import IdfBase
import hub.exports.building_energy.idf_helper as idf_cte


class IdfOutput(IdfBase):
  @staticmethod
  def add(cerc_idf):
    output_table_file = str(Path(cerc_idf.idf_file_path).parent / 'output_table.idf')
    with open(output_table_file, 'r', encoding='UTF-8') as base_idf:
      cerc_idf.idf_file.writelines(base_idf.readlines())
    if cerc_idf.outputs is None or (
      cerc_idf.outputs['output_meters'] is None and cerc_idf.outputs['output_variables'] is None):
      outputs_file_path = str(Path(cerc_idf.idf_file_path).parent / 'outputs.idf')
      with open(outputs_file_path, 'r', encoding='UTF-8') as outputs_idf:
        cerc_idf.idf_file.writelines(outputs_idf.readlines())
    else:
      for output_meter in cerc_idf.outputs['output_meters']:
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, idf_cte.METER)
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, output_meter['name'], 'Key Name')
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, output_meter['frequency'], 'Reporting Frequency', ';')
      for output_variable in cerc_idf.outputs['output_variables']:
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, idf_cte.VARIABLE)
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, output_variable['key_value'], 'Key Value')
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, output_variable['name'], 'Variable Name')
        cerc_idf.write_to_idf_format(cerc_idf.idf_file, output_variable['frequency'], 'Reporting Frequency', ';')
    return
