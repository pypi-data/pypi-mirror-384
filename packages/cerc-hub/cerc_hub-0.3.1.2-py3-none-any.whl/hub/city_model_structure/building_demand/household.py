"""
Household module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class Household:
  """
  Household class
  """

  def __init__(self):
    self._number_of_people = None
    self._number_of_cars = None

  @property
  def number_of_people(self):
    """
    Get number of people leaving in the household
    :return: int
    """
    return self._number_of_people

  @property
  def number_of_cars(self):
    """
    Get number of cars owned by the householders
    :return: int
    """
    return self._number_of_cars
