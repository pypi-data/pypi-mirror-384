import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfOutputControlFiles(IdfBase):
  _file_outputs = ['CSV', 'MTR', 'ESO', 'EIO', 'Tabular', 'SQLite', 'JSON', 'AUDIT', 'Zone Sizing', 'System Sizing',
                   'DXF', 'BND', 'RDD', 'MDD', 'MTD', 'END', 'SHD', 'DFS', 'GLHE', 'DelightIn', 'DelightELdmp',
                   'DelightDFdmp', 'EDD', 'DBG', 'PerfLog', 'SLN', 'SCI', 'WRL', 'Screen', 'ExtShd', 'Tarcog']

  @staticmethod
  def add(cerc_idf):

    if cerc_idf.outputs is None or 'control_files' not in cerc_idf.outputs:
      return
    last_file_format = IdfOutputControlFiles._file_outputs[-1]
    print(last_file_format)
    file = cerc_idf.files['control_files']
    cerc_idf.write_to_idf_format(file, idf_cte.CONTROL_FILES)
    for control_file in IdfOutputControlFiles._file_outputs:
      should_output = 'No'
      if control_file in cerc_idf.outputs['control_files']:
        should_output = 'Yes'
      if control_file == last_file_format:
        cerc_idf.write_to_idf_format(file, should_output, f'Output {control_file}', ';')
      else:
        cerc_idf.write_to_idf_format(file, should_output, f'Output {control_file}')
