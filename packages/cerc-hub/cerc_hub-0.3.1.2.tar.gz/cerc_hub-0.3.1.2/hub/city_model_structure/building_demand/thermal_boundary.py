"""
ThermalBoundary module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import uuid
import math
from typing import List, Union, TypeVar
import logging
from hub.helpers.configuration_helper import ConfigurationHelper as ch
import hub.helpers.constants as cte
from hub.city_model_structure.building_demand.layer import Layer
from hub.city_model_structure.building_demand.thermal_opening import ThermalOpening
from hub.city_model_structure.building_demand.thermal_zone import ThermalZone

Surface = TypeVar('Surface')


class ThermalBoundary:
  """
  ThermalBoundary class
  """
  def __init__(self, parent_surface, opaque_area, windows_areas):
    self._parent_surface = parent_surface
    self._opaque_area = opaque_area
    self._windows_areas = windows_areas
    self._id = None
    self._thermal_zones = None
    self._thermal_openings = None
    self._layers = None
    self._he = ch().convective_heat_transfer_coefficient_exterior
    self._hi = ch().convective_heat_transfer_coefficient_interior
    self._u_value = None
    self._construction_name = None
    self._thickness = None
    self._internal_surface = None
    self._external_surface = None
    self._window_ratio = 0
    self._window_ratio_to_be_calculated = False
    if self._windows_areas is not None:
      self._window_ratio_to_be_calculated = True

  @property
  def id(self):
    """
    Get thermal zone id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def parent_surface(self) -> Surface:
    """
    Get the surface that belongs to the thermal boundary, considered the external surface of that boundary
    :return: Surface
    """
    return self._parent_surface

  @property
  def thermal_zones(self) -> List[ThermalZone]:
    """
    Get the thermal zones delimited by the thermal boundary
    :return: [ThermalZone]
    """
    return self._thermal_zones

  @thermal_zones.setter
  def thermal_zones(self, value):
    """
    Get the thermal zones delimited by the thermal boundary
    :param value: [ThermalZone]
    """
    self._thermal_zones = value

  @property
  def opaque_area(self):
    """
    Get the thermal boundary area in square meters
    :return: float
    """
    return float(self._opaque_area)

  @property
  def thickness(self):
    """
    Get the thermal boundary thickness in meters
    :return: float
    """
    if self._thickness is None:
      self._thickness = 0.0
      if self.layers is not None:
        for layer in self.layers:
          if not layer.no_mass:
            self._thickness += layer.thickness
    return self._thickness

  @property
  def thermal_openings(self) -> Union[None, List[ThermalOpening]]:
    """
    Get thermal boundary thermal openings
    :return: None or [ThermalOpening]
    """
    if self._thermal_openings is None:
      if self.windows_areas is not None:
        if len(self.windows_areas) > 0:
          self._thermal_openings = []
          for window_area in self.windows_areas:
            thermal_opening = ThermalOpening()
            thermal_opening.area = window_area
            self._thermal_openings.append(thermal_opening)
        else:
          self._thermal_openings = []
      else:
        if self.window_ratio is not None:
          if self.window_ratio == 0:
            self._thermal_openings = []
          else:
            thermal_opening = ThermalOpening()
            if self.window_ratio == 1:
              _area = self.opaque_area
            else:
              _area = self.opaque_area * self.window_ratio / (1-self.window_ratio)
            thermal_opening.area = _area
            self._thermal_openings = [thermal_opening]
        else:
          self._thermal_openings = []
    else:
      if self.windows_areas is not None:
        return self._thermal_openings
      if self.window_ratio is not None:
        if self.window_ratio == 0:
          self._thermal_openings = []
        else:
          if len(self._thermal_openings) == 0:
            thermal_opening = ThermalOpening()
            if self.window_ratio == 1:
              _area = self.opaque_area
            else:
              _area = self.opaque_area * self.window_ratio / (1-self.window_ratio)
            thermal_opening.area = _area
            self._thermal_openings = [thermal_opening]
          else:
            for _thermal_opening in self._thermal_openings:
              if self.window_ratio == 1:
                _area = self.opaque_area
              else:
                _area = self.opaque_area * self.window_ratio / (1-self.window_ratio)
              _thermal_opening.area = _area
              self._thermal_openings = [_thermal_opening]
    for thermal_opening in self._thermal_openings:
      opening_name = 'Window'
      if self.parent_surface.type != 'Wall':
        opening_name = 'Skylight'
      thermal_opening.construction_name = f'{opening_name}_{self._construction_archetype.name}'
      thermal_opening.g_value = self._construction_archetype.window_g_value
      thermal_opening.overall_u_value = self._construction_archetype.window_overall_u_value
      thermal_opening.frame_ratio = self._construction_archetype.window_frame_ratio
    return self._thermal_openings

  @property
  def _construction_archetype(self):
    if self.thermal_zones is None:
      return None
    construction_archetypes = self.thermal_zones[0].parent_internal_zone.thermal_archetype.constructions
    for construction_archetype in construction_archetypes:
      if str(self.type) == str(construction_archetype.type):
        return construction_archetype

  @property
  def layers(self) -> List[Layer]:
    """
    Get thermal boundary layers
    :return: [Layers]
    """
    if self._construction_archetype is not None:
      self._layers = self._construction_archetype.layers
    else:
      logging.error('Layers not defined\n')
      return None
    return self._layers

  @property
  def type(self):
    """
    Get thermal boundary surface type
    :return: str
    """
    return self.parent_surface.type

  @property
  def window_ratio(self) -> Union[None, float]:
    """
    Get thermal boundary window ratio
    It returns the window ratio calculated as the total windows' areas in a wall divided by
    the total (opaque + transparent) area of that wall if windows are defined in the geometry imported.
    If not, it returns the window ratio imported from an external source (e.g. construction library, manually assigned).
    If none of those sources are available, it returns None.
    :return: float
    """
    if self._window_ratio_to_be_calculated:
      if len(self.windows_areas) == 0:
        self._window_ratio = 0
      else:
        total_window_area = 0
        for window_area in self.windows_areas:
          total_window_area += window_area
        self._window_ratio = total_window_area / (self.opaque_area + total_window_area)
    else:
      if self.type in (cte.WALL, cte.ROOF):
        if -math.sqrt(2) / 2 < math.sin(self.parent_surface.azimuth) < math.sqrt(2) / 2:
          if 0 < math.cos(self.parent_surface.azimuth):
            self._window_ratio = \
              float(self._construction_archetype.window_ratio['north']) / 100
          else:
            self._window_ratio = \
              float(self._construction_archetype.window_ratio['south']) / 100
        elif math.sqrt(2) / 2 <= math.sin(self._parent_surface.azimuth):
          self._window_ratio = \
            float(self._construction_archetype.window_ratio['east']) / 100
        else:
          self._window_ratio = \
            float(self._construction_archetype.window_ratio['west']) / 100
    return self._window_ratio

  @property
  def windows_areas(self) -> [float]:
    """
    Get windows areas
    :return: [float]
    """
    return self._windows_areas

  @property
  def u_value(self) -> Union[None, float]:
    """
    Get thermal boundary U-value in W/m2K
    internal and external convective coefficient in W/m2K values, can be configured at configuration.ini
    :return: None or float
    """
    if self._u_value is None:
      h_i = self.hi
      h_e = self.he
      if self.type == cte.GROUND:
        r_value = 1.0 / h_i + ch().soil_thickness / ch().soil_conductivity
      else:
        r_value = 1.0/h_i + 1.0/h_e
      try:
        for layer in self.layers:
          if layer.no_mass:
            r_value += float(layer.thermal_resistance)
          else:
            r_value += float(layer.thickness) / float(layer.conductivity)
        self._u_value = 1.0/r_value
      except TypeError:
        raise TypeError('Constructions layers are not initialized') from TypeError
    return self._u_value

  @property
  def construction_name(self):
    """
    Get construction name
    :return: str
    """
    if self._construction_archetype is not None:
      self._construction_name = self._construction_archetype.name
    else:
      logging.error('Construction name not defined\n')
      raise ValueError('Construction name not defined')
    return self._construction_name

  @u_value.setter
  def u_value(self, value):
    """
    Set thermal boundary U-value in W/m2K
    :param value: float
    """
    if value is not None:
      self._u_value = float(value)

  @property
  def hi(self) -> Union[None, float]:
    """
    Get internal convective heat transfer coefficient (W/m2K)
    :return: None or float
    """
    return self._hi

  @hi.setter
  def hi(self, value):
    """
    Set internal convective heat transfer coefficient (W/m2K)
    :param value: float
    """
    if value is not None:
      self._hi = value

  @property
  def he(self) -> Union[None, float]:
    """
    Get external convective heat transfer coefficient (W/m2K)
    :return: None or float
    """
    return self._he

  @he.setter
  def he(self, value):
    """
    Set external convective heat transfer coefficient (W/m2K)
    :param value: float
    """
    if value is not None:
      self._he = value

  @property
  def internal_surface(self) -> Surface:
    """
    Get the internal surface of the thermal boundary
    :return: Surface
    """
    if self._internal_surface is None:
      self._internal_surface = self.parent_surface.inverse
      # The agreement is that the layers are defined from outside to inside
      internal_layer = self.layers[len(self.layers) - 1]
      self._internal_surface.short_wave_reflectance = 1 - internal_layer.solar_absorptance
      self._internal_surface.long_wave_emittance = 1 - internal_layer.solar_absorptance

    return self._internal_surface

  @property
  def external_surface(self) -> Surface:
    if self._external_surface is None:
      # The agreement is that the layers are defined from outside to inside
      self._external_surface = self.parent_surface
      self._external_surface.short_wave_reflectance = 1 - self.layers[0].solar_absorptance
      self._external_surface.long_wave_emittance = 1 - self.layers[0].solar_absorptance
    return self._external_surface
