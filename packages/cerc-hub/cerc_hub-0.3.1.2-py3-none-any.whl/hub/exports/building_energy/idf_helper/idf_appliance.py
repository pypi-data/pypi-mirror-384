"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfAppliance(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    schedule_name = f'Appliance schedules {thermal_zone.usage_name}'
    schedule_name = cerc_idf.schedules_added_to_idf[schedule_name]
    storeys_number = int(thermal_zone.total_floor_area / thermal_zone.footprint_area)
    watts_per_zone_floor_area = thermal_zone.appliances.density * storeys_number
    subcategory = f'ELECTRIC EQUIPMENT#{zone_name}#InteriorEquipment'
    file = cerc_idf.files['appliances']
    cerc_idf.write_to_idf_format(file, idf_cte.APPLIANCES)
    cerc_idf.write_to_idf_format(file, zone_name, 'Name')
    cerc_idf.write_to_idf_format(file, 'Electricity', 'Fuel Type')
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone or ZoneList or Space or SpaceList Name')
    cerc_idf.write_to_idf_format(file, schedule_name, 'Schedule Name')
    cerc_idf.write_to_idf_format(file, 'Watts/Area', 'Design Level Calculation Method')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Design Level')
    cerc_idf.write_to_idf_format(file, watts_per_zone_floor_area, 'Power per Zone Floor Area')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Power per Person')
    cerc_idf.write_to_idf_format(file, thermal_zone.appliances.latent_fraction, 'Fraction Latent')
    cerc_idf.write_to_idf_format(file, thermal_zone.appliances.radiative_fraction, 'Fraction Radiant')
    cerc_idf.write_to_idf_format(file, 0, 'Fraction Lost')
    cerc_idf.write_to_idf_format(file, 0, 'Carbon Dioxide Generation Rate')
    cerc_idf.write_to_idf_format(file, subcategory, 'EndUse Subcategory', ';')
