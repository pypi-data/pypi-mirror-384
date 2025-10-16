"""
Hub CO2 Analysis catalog content
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""


class Content:
  """
  Content class
  """
  def __init__(self,
               embodied_co2_material,
               embodied_co2_window,
               end_of_life_co2_material,
               end_of_life_co2_window):
    self._embodied_co2_material = embodied_co2_material
    self._embodied_co2_window = embodied_co2_window
    self._end_of_life_co2_material = end_of_life_co2_material
    self._end_of_life_co2_window = end_of_life_co2_window

  @property
  def embodied_co2_material(self):
    """
    :getter: Get all materials with their corresponding Embodied CO2 values
    :return: dict
    """
    return self._embodied_co2_material

  @property
  def embodied_co2_window(self):
    """
    :getter: Get all windows with their corresponding Embodied CO2 values
    :return: dict
    """
    return self._embodied_co2_window

  @property
  def end_of_life_co2_material(self):
    """
    :getter: Get all materials with their corresponding end-of-life CO2 values
    :return: dict
    """
    return self._end_of_life_co2_material

  @property
  def end_of_life_co2_window(self):
    """
    :getter: Get all windows with their corresponding end-of-life CO2 values
    :return: dict
    """
    return self._end_of_life_co2_window

  def to_dictionary(self):
    """
    Combine all class attributes into a single dictionary
    """
    embodied_co2_windows = []
    embodied_co2_materials = []
    end_of_life_co2_windows = []
    end_of_life_co2_materials = []

    for window in self.embodied_co2_window:
      embodied_co2_windows.append(window.to_dictionary())
    for material in self.embodied_co2_material:
      embodied_co2_materials.append(material.to_dictionary())
    for window in self.end_of_life_co2_window:
      end_of_life_co2_windows.append(window.to_dictionary())
    for material in self.end_of_life_co2_material:
      end_of_life_co2_materials.append(material.to_dictionary())

    content = {
      'embodied_co2_window': embodied_co2_windows,
      'embodied_co2_material': embodied_co2_materials,
      'end_of_life_co2_window': end_of_life_co2_windows,
      'end_of_life_co2_material': end_of_life_co2_materials
    }
    return content

  def __str__(self):
    """
    Print class attributes as a string
    """
    embodied_co2_windows = []
    embodied_co2_materials = []
    end_of_life_co2_windows = []
    end_of_life_co2_materials = []

    for window in self.embodied_co2_window:
      embodied_co2_windows.append(window.to_dictionary())
    for material in self.embodied_co2_material:
      embodied_co2_materials.append(material.to_dictionary())
    for window in self.end_of_life_co2_window:
      end_of_life_co2_windows.append(window.to_dictionary())
    for material in self.end_of_life_co2_material:
      end_of_life_co2_materials.append(material.to_dictionary())

    content = {
      'embodied_co2_window': embodied_co2_windows,
      'embodied_co2_material': embodied_co2_materials,
      'end_of_life_co2_window': end_of_life_co2_windows,
      'end_of_life_co2_material': end_of_life_co2_materials
    }
    return str(content)
