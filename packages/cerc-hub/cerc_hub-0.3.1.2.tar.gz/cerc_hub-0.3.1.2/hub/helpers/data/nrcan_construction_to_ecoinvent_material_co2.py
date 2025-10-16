"""
Dictionaries module for NRCAN construction to Hub material CO2 emissions
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""

class NrcanConstructionToEcoinventMaterialCo2:
  """
  NRCAN construction to Hub material CO2 emissions class
  """
  def __init__(self):
    self._dictionary = {
      "Urea Formaldehyde Foam": {
        "name": "urea_formaldehyde_foam",
        "factor": 1.0
      },
      "Cast Concrete": {
        "name": "cast_concrete",
        "factor": 1.0
      },
      "Floor/Roof Screed": {
        "name": "screed_floor_roof",
        "factor": 1.0
      },
      "Timber Flooring": {
        "name": "timber_flooring",
        "factor": 1.0
      },
      "Asphalt 1": {
        "name": "asphalt",
        "factor": 1.0
      },
      "MW Glass Wool (rolls)": {
        "name": "mw_glass_wool",
        "factor": 1.0
      },
      "Plasterboard": {
        "name": "plasterboard",
        "factor": 1.0
      },
      "Brickwork Outer": {
        "name": "outer_brickwork",
        "factor": 1.0
      },
      "XPS Extruded Polystyrene- CO2 Blowing": {
        "name": "xps_extruded_polystyrene",
        "factor": 1.0
      },
      "Concrete Block (Medium)": {
        "name": "medium_concrete_block",
        "factor": 1.0
      },
      "Gypsum Plastering": {
        "name": "gypsum_plastering",
        "factor": 1.0
      },
      "Lightweight Metallic Cladding": {
        "name": "lightweight_metallic_cladding",
        "factor": 1.0
      },
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
