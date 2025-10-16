"""
Energy System catalog content
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class Content:
  """
  Content class
  """
  def __init__(self, archetypes, systems, generations=None, distributions=None):
    self._archetypes = archetypes
    self._systems = systems
    self._generations = generations
    self._distributions = distributions

  @property
  def archetypes(self):
    """
    All archetype system clusters in the catalog
    """
    return self._archetypes

  @property
  def systems(self):
    """
    All systems in the catalog
    """
    return self._systems

  @property
  def generation_equipments(self):
    """
    All generation equipments in the catalog
    """
    return self._generations

  @property
  def distribution_equipments(self):
    """
    All distribution equipments in the catalog
    """
    return self._distributions

  def to_dictionary(self):
    """Class content to dictionary"""
    _archetypes = []
    for _archetype in self.archetypes:
      _archetypes.append(_archetype.to_dictionary())
    content = {'Archetypes': _archetypes}

    return content

  def __str__(self):
    """Print content"""
    _archetypes = []
    for _archetype in self.archetypes:
      _archetypes.append(_archetype.to_dictionary())
    content = {'Archetypes': _archetypes}

    return str(content)
