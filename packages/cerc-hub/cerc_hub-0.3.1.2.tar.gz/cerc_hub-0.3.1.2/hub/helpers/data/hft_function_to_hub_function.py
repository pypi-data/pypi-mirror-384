"""
Dictionaries module for Hft function to hub function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class HftFunctionToHubFunction:
  """
  Hft function to hub function class
  """
  def __init__(self):
    self._dictionary = {
      'residential': cte.RESIDENTIAL,
      'single family house': cte.SINGLE_FAMILY_HOUSE,
      'multifamily house': cte.MULTI_FAMILY_HOUSE,
      'hotel': cte.HOTEL,
      'hospital': cte.HOSPITAL,
      'outpatient': cte.OUT_PATIENT_HEALTH_CARE,
      'commercial': cte.SUPERMARKET,
      'strip mall': cte.STRIP_MALL,
      'warehouse': cte.WAREHOUSE,
      'primary school': cte.PRIMARY_SCHOOL,
      'secondary school': cte.EDUCATION,
      'office': cte.MEDIUM_OFFICE,
      'large office': cte.LARGE_OFFICE
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
