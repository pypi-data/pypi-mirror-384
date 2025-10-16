"""
Greenery catalog content
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""


class Content:
  """
  Content class
  """
  def __init__(self, vegetations, plants, soils):
    self._vegetations = vegetations
    self._plants = plants
    self._soils = soils

  @property
  def vegetations(self):
    """
    All vegetation in the catalog
    """
    return self._vegetations

  @property
  def plants(self):
    """
    All plants in the catalog
    """
    return self._plants

  @property
  def soils(self):
    """
    All soils in the catalog
    """
    return self._soils

  def to_dictionary(self):
    """Class content to dictionary"""
    _archetypes = []
    for _archetype in self.vegetations:
      _archetypes.append(_archetype.to_dictionary())
    content = {'Archetypes': _archetypes}

    return content

  def __str__(self):
    """Print content"""
    _archetypes = []
    for _archetype in self.vegetations:
      _archetypes.append(_archetype.to_dictionary())
    content = {'Archetypes': _archetypes}

    return str(content)
