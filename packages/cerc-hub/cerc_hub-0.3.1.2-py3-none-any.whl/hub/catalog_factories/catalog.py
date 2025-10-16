"""
Catalog base class
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""


class Catalog:
  """
  Catalogs base class
  catalog_factories will inherit from this class.
  """

  def names(self, category=None):
    """
    Base property to return the catalog entries names.
    :return: Catalog names filter by category if provided
    """
    raise NotImplementedError

  def entries(self, category=None):
    """
    Base property to return the catalog entries
    :return: Catalog content filter by category if provided
    """
    raise NotImplementedError

  def get_entry(self, name):
    """
    Base property to return the catalog entry matching the given name
    :return: Catalog entry with the matching name
    """
    raise NotImplementedError
