"""
Dictionaries module saves all transformations of functions and usages to access the catalogs
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.helpers.parsers.list_usage_to_hub import ListUsageToHub
from hub.helpers.parsers.string_usage_to_hub import StringUsageToHub 

class UsageParsers:
  """
  Dictionaries class
  """

  @staticmethod
  def string_usage_to_hub() -> object:
    """
    Hub usage to HfT usage, transformation dictionary
    :return: dict
    """
    return StringUsageToHub().parse

  @staticmethod
  def list_usage_to_hub(function_dictionary=None) -> object:
    """
    Hub usage to HfT usage, transformation dictionary
    :return: dict
    """
    return ListUsageToHub(function_dictionary).parse

