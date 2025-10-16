"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import uuid
from pathlib import Path

import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfFileSchedule(IdfBase):
  @staticmethod
  def add(cerc_idf, usage, schedule_type, schedules):
    schedule_name = f'{schedule_type} schedules {usage}'
    for schedule in schedules:
      if schedule_name not in cerc_idf.schedules_added_to_idf:
        cerc_idf.schedules_added_to_idf[schedule_name] = uuid.uuid4()
        file_name = str(
          (Path(cerc_idf.output_path) / f'{cerc_idf.schedules_added_to_idf[schedule_name]}.csv').resolve())
        with open(file_name, 'w', encoding='utf8') as file:
          for value in schedule.values[0]:
            file.write(f'{value},\n')
        file = cerc_idf.files['file_schedules']
        cerc_idf.write_to_idf_format(file, idf_cte.FILE_SCHEDULE)
        cerc_idf.write_to_idf_format(file, cerc_idf.schedules_added_to_idf[schedule_name], 'Name')
        cerc_idf.write_to_idf_format(file, idf_cte.idf_type_limits[schedule.data_type], 'Schedule Type Limits Name')
        cerc_idf.write_to_idf_format(file, Path(file_name).name, 'File Name')
        cerc_idf.write_to_idf_format(file, 1, 'Column Number')
        cerc_idf.write_to_idf_format(file, 0, 'Rows to Skip at Top')
        cerc_idf.write_to_idf_format(file, 8760, 'Number of Hours of Data')
        cerc_idf.write_to_idf_format(file, 'Comma', 'Column Separator')
        cerc_idf.write_to_idf_format(file, 'No', 'Interpolate to Timestep')
        cerc_idf.write_to_idf_format(file, '60', 'Minutes per Item')
        cerc_idf.write_to_idf_format(file, 'Yes', 'Adjust Schedule for Daylight Savings', ';')
