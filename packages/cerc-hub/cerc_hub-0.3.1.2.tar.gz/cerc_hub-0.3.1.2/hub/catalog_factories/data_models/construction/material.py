"""
Construction catalog material
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""


class Material:
  """
  Material class
  """
  def __init__(self, material_id,
               name,
               solar_absorptance,
               thermal_absorptance,
               visible_absorptance,
               no_mass=False,
               thermal_resistance=None,
               conductivity=None,
               density=None,
               specific_heat=None):
    self._id = material_id
    self._name = name
    self._solar_absorptance = solar_absorptance
    self._thermal_absorptance = thermal_absorptance
    self._visible_absorptance = visible_absorptance
    self._no_mass = no_mass
    self._thermal_resistance = thermal_resistance
    self._conductivity = conductivity
    self._density = density
    self._specific_heat = specific_heat

  @property
  def id(self):
    """
    Get material id
    :return: str
    """
    return self._id

  @property
  def name(self):
    """
    Get material name
    :return: str
    """
    return self._name

  @property
  def conductivity(self):
    """
    Get material conductivity in W/mK
    :return: None or float
    """
    return self._conductivity

  @property
  def specific_heat(self):
    """
    Get material conductivity in J/kgK
    :return: None or float
    """
    return self._specific_heat

  @property
  def density(self):
    """
    Get material density in kg/m3
    :return: None or float
    """
    return self._density

  @property
  def solar_absorptance(self):
    """
    Get material solar absorptance
    :return: None or float
    """
    return self._solar_absorptance

  @property
  def thermal_absorptance(self):
    """
    Get material thermal absorptance
    :return: None or float
    """
    return self._thermal_absorptance

  @property
  def visible_absorptance(self):
    """
    Get material visible absorptance
    :return: None or float
    """
    return self._visible_absorptance

  @property
  def no_mass(self):
    """
    Get material no mass flag
    :return: None or Boolean
    """
    return self._no_mass

  @property
  def thermal_resistance(self):
    """
    Get material thermal resistance in m2K/W
    :return: None or float
    """
    return self._thermal_resistance

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Material': {'id': self.id,
                            'name': self.name,
                            'is no-mass': self.no_mass,
                            'density [kg/m3]': self.density,
                            'specific heat [J/kgK]': self.specific_heat,
                            'conductivity [W/mK]': self.conductivity,
                            'thermal resistance [m2K/W]': self.thermal_resistance,
                            'solar absorptance': self.solar_absorptance,
                            'thermal absorptance': self.thermal_absorptance,
                            'visible absorptance': self.visible_absorptance
                            }
               }
    return content
