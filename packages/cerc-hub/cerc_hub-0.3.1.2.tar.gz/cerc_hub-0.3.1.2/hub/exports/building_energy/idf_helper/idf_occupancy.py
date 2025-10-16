import hub.exports.building_energy.idf_helper as idf_cte
from hub.exports.building_energy.idf_helper.idf_base import IdfBase


class IdfOccupancy(IdfBase):
  @staticmethod
  def add(cerc_idf, thermal_zone, zone_name):
    number_of_people = thermal_zone.occupancy.occupancy_density * thermal_zone.total_floor_area
    fraction_radiant = 0
    total_sensible = (
      thermal_zone.occupancy.sensible_radiative_internal_gain + thermal_zone.occupancy.sensible_convective_internal_gain
    )
    if total_sensible != 0:
      fraction_radiant = thermal_zone.occupancy.sensible_radiative_internal_gain / total_sensible
    occupancy_schedule_name = f'Occupancy schedules {thermal_zone.usage_name}'
    activity_level_schedule_name = f'Activity Level schedules {thermal_zone.usage_name}'
    occupancy_schedule = cerc_idf.schedules_added_to_idf[occupancy_schedule_name]
    activity_level_schedule = cerc_idf.schedules_added_to_idf[activity_level_schedule_name]
    file = cerc_idf.files['occupancy']
    cerc_idf.write_to_idf_format(file, idf_cte.PEOPLE)
    cerc_idf.write_to_idf_format(file, f'{zone_name}_occupancy', 'Name')
    cerc_idf.write_to_idf_format(file, zone_name, 'Zone or ZoneList or Space or SpaceList Name')
    cerc_idf.write_to_idf_format(file, occupancy_schedule, 'Number of People Schedule Name')
    cerc_idf.write_to_idf_format(file, 'People', 'Number of People Calculation Method')
    cerc_idf.write_to_idf_format(file, number_of_people, 'Number of People')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'People per Floor Area')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Floor Area per Person')
    cerc_idf.write_to_idf_format(file, fraction_radiant, 'Fraction Radiant')
    cerc_idf.write_to_idf_format(file, idf_cte.AUTOCALCULATE, 'Sensible Heat Fraction')
    cerc_idf.write_to_idf_format(file, activity_level_schedule, 'Activity Level Schedule Name')
    cerc_idf.write_to_idf_format(file, '3.82e-08', 'Carbon Dioxide Generation Rate')
    cerc_idf.write_to_idf_format(file, 'No', 'Enable ASHRAE 55 Comfort Warnings')
    cerc_idf.write_to_idf_format(file, 'EnclosureAveraged', 'Mean Radiant Temperature Calculation Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Surface NameAngle Factor List Name')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Work Efficiency Schedule Name')
    cerc_idf.write_to_idf_format(file, 'ClothingInsulationSchedule', 'Clothing Insulation Calculation Method')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Clothing Insulation Calculation Method Schedule Name')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Clothing Insulation Schedule Name')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Air Velocity Schedule Name')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 1 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 2 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 3 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 4 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 5 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 6 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Thermal Comfort Model 7 Type')
    cerc_idf.write_to_idf_format(file, idf_cte.EMPTY, 'Ankle Level Air Velocity Schedule Name')
    cerc_idf.write_to_idf_format(file, '15.56', 'Cold Stress Temperature Threshold')
    cerc_idf.write_to_idf_format(file, '30', 'Heat Stress Temperature Threshold', ';')
