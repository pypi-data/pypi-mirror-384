"""
Dictionaries module for hub usage to Palma usage
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Cecilia Pérez cperez@irec.cat
"""

"""
Codification of uses from cadastre:
U: store-parking. Residential Use
S: store-parking. Industrial Use
V: Residential
I: Industrial
O: Offices
C: Comercial
K: Sportive center
T: Shows
G: Leisure and Hostelry
Y: Health and charity
E: Culture
R: Religion
M: Urbanization work, gardening and undeveloped land
P: Singular building 
B: Farm warehouse
J: Farm Industry
Z: Farm-related
"""

import hub.helpers.constants as cte

class HubUsageToPalmaUsage:
  """
  Hub usage to Palma usage class
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'residential',
      cte.SINGLE_FAMILY_HOUSE: 'residential',
      cte.HIGH_RISE_APARTMENT: 'residential',
      cte.MID_RISE_APARTMENT: 'residential',
      cte.MULTI_FAMILY_HOUSE: 'residential'
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
