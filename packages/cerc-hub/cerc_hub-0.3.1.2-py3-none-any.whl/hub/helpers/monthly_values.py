"""
Monthly values module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2020 Project Author Pilar Monsalvete pilar_monsalvete@yahoo.es
"""

import hub.helpers.constants as cte


class MonthlyValues:
  """
  Monthly values class
  """
  @staticmethod
  def get_mean_values(values):
    """
    Calculates the mean values for each month from a list with hourly values
    :return: [float] x 12
    :param values: [float] x 8760
    """
    out = []
    if values is not None:
      hour = 0
      for month in cte.DAYS_A_MONTH:
        total = 0
        for _ in range(0, cte.DAYS_A_MONTH[month]):
          for _ in range(0, 24):
            total += values[hour] / 24 / cte.DAYS_A_MONTH[month]
            hour += 1
        out.append(total)
    return out

  @staticmethod
  def get_total_month(values):
    """
    Calculates the total value for each month
    :return: [float] x 12
    :param values: [float] x 8760
    """
    out = []
    if values is not None:
      hour = 0
      for month in cte.DAYS_A_MONTH:
        total = 0
        for _ in range(0, cte.DAYS_A_MONTH[month]):
          for _ in range(0, 24):
            total += values[hour]
            hour += 1
        out.append(total)
    return out
