"""
Dictionaries module for Montreal system to hub energy generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class MontrealSystemToHubEnergyGenerationSystem:
  """
  Montreal's system to hub energy generation system class
  """
  def __init__(self):
    self._dictionary = {
      'Unitary air conditioner with baseboard heater fuel fired boiler': cte.BOILER,
      'Unitary air conditioner with baseboard heater electrical boiler': cte.BOILER,
      '4 pipe fan coils with fuel fired boiler': cte.BOILER,
      '4 pipe fan coils with electrical resistance water boiler': cte.BOILER,
      'Single zone packaged rooftop unit with fuel-fired furnace and baseboards and fuel boiler for acs': cte.BOILER,
      'Single zone packaged rooftop unit with electrical resistance furnace and baseboards and fuel boiler for acs': cte.BOILER,
      'Single zone make-up air unit with baseboard heating with fuel fired boiler': cte.BOILER,
      'Single zone make-up air unit with electrical baseboard heating and DHW with resistance': cte.BASEBOARD,
      'Multi-zone built-up system with baseboard heater hydronic with fuel fired boiler': cte.BOILER,
      'Multi-zone built-up system with electrical baseboard heater and electrical hot water': cte.BASEBOARD,
      'Unitary air conditioner air cooled DX with external condenser': cte.CHILLER,
      '4 pipe fan coils with water cooled, water chiller': cte.CHILLER,
      'Single zone packaged rooftop unit with air cooled DX': cte.CHILLER,
      'Single zone make-up air unit with air cooled DX': cte.CHILLER,
      'Multi-zone built-up system with water cooled, water chiller': cte.CHILLER,
      'PV system': cte.PHOTOVOLTAIC,
      'Multi-zone built-up system with heat pump for cooling': cte.CHILLER,
      'Multi-zone built-up system with heat pump for heat': cte.HEAT_PUMP
                        }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
