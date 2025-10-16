"""
Hub End-of-Life CO2 catalog for materials
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""


class EndOfLifeCo2Material:
  """
  EndOfLifeCo2Material class
  """
  def __init__(self,
               name,
               recycling_ratio,
               onsite_recycling_ratio,
               company_recycling_ratio,
               landfilling_ratio,
               demolition_machine_emission,
               onsite_machine_emission,
               companies_recycling_machine_emission,
               landfilling_machine_emission):
    self._name = name
    self._recycling_ratio = recycling_ratio
    self._onsite_recycling_ratio = onsite_recycling_ratio
    self._company_recycling_ratio = company_recycling_ratio
    self._landfilling_ratio = landfilling_ratio
    self._demolition_machine_emission = demolition_machine_emission
    self._onsite_machine_emission = onsite_machine_emission
    self._companies_recycling_machine_emission = companies_recycling_machine_emission
    self._landfilling_machine_emission = landfilling_machine_emission

  @property
  def name(self):
    """
    :getter: Get material name
    :return: str
    """
    return self._name

  @property
  def recycling_ratio(self):
    """
    :getter: Get recycling ratio of material
    :return: None or float
    """
    return self._recycling_ratio

  @property
  def onsite_recycling_ratio(self):
    """
    :getter: Get onsite recycling ratio of material
    :return: None or float
    """
    return self._onsite_recycling_ratio

  @property
  def company_recycling_ratio(self):
    """
    :getter: Get company recycling ratio of material
    :return: None or float
    """
    return self._company_recycling_ratio

  @property
  def landfilling_ratio(self):
    """
    :getter: Get landfilling ratio of material
    :return: None or float
    """
    return self._landfilling_ratio

  @property
  def demolition_machine_emission(self):
    """
    :getter: Get demolition machine emissions factor of material
    :return: None or float
    """
    return self._demolition_machine_emission

  @property
  def onsite_machine_emission(self):
    """
    :getter: Get onsite machine emissions factor of material
    :return: None or float
    """
    return self._onsite_machine_emission

  @property
  def companies_recycling_machine_emission(self):
    """
    :getter: Get companies recycling machine emissions factor of material
    :return: None or float
    """
    return self._companies_recycling_machine_emission

  @property
  def landfilling_machine_emission(self):
    """
    :getter: Get landfilling machine emissions factor of material
    :return: None or float
    """
    return self._landfilling_machine_emission

  def to_dictionary(self):
    """
    Convert class attributes to a dictionary
    :return: dict
    """
    content = {'Material': {'name': self.name,
                            'recycling_ratio': self.recycling_ratio,
                            'onsite_recycling_ratio': self.onsite_recycling_ratio,
                            'company_recycling_ratio': self.company_recycling_ratio,
                            'landfilling_ratio': self.landfilling_ratio,
                            'demolition_machine_emission': self.demolition_machine_emission,
                            'onsite_machine_emission': self.onsite_machine_emission,
                            'companies_recycling_machine_emission': self.companies_recycling_machine_emission,
                            'landfilling_machine_emission': self.landfilling_machine_emission
                           }
               }
    return content
