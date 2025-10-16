"""
Greenery catalog data model Vegetation class
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.catalog_factories.data_models.greenery.plant_percentage import PlantPercentage


class Vegetation:
  """
  Vegetation class
  """
  def __init__(self, category, vegetation, plant_percentages):
    self._name = vegetation.name
    self._category = category
    self._soil_thickness = vegetation.thicknessOfSoil
    self._management = vegetation.management
    self._air_gap = vegetation.airGap
    self._soil_name = vegetation.soil.name
    self._soil_roughness = vegetation.soil.roughness
    self._dry_soil_conductivity = vegetation.soil.conductivityOfDrySoil
    self._dry_soil_density = vegetation.soil.densityOfDrySoil
    self._dry_soil_specific_heat = vegetation.soil.specificHeatOfDrySoil
    self._soil_thermal_absorptance = vegetation.soil.thermalAbsorptance
    self._soil_solar_absorptance = vegetation.soil.solarAbsorptance
    self._soil_visible_absorptance = vegetation.soil.visibleAbsorptance
    self._soil_saturation_volumetric_moisture_content = vegetation.soil.saturationVolumetricMoistureContent
    self._soil_residual_volumetric_moisture_content = vegetation.soil.residualVolumetricMoistureContent
    self._soil_initial_volumetric_moisture_content = vegetation.soil.initialVolumetricMoistureContent
    self._plant_percentages = plant_percentages

  @property
  def name(self):
    """
    Get vegetation name
    :return: string
    """
    return self._name

  @property
  def category(self):
    """
    Get vegetation category
    :return: string
    """
    return self._category

  @property
  def soil_thickness(self):
    """
    Get soil thickness in m
    :return: float
    """
    return self._soil_thickness

  @property
  def management(self):
    """
    Get management
    :return: string
    """
    return self._management

  @property
  def air_gap(self):
    """
    Get air gap in m
    :return: float
    """
    return self._air_gap

  @property
  def plant_percentages(self) -> [PlantPercentage]:
    """
    Get plant percentages
    :return: [PlantPercentage]
    """
    percentage = 0.0
    for plant_percentage in self._plant_percentages:
      percentage += float(plant_percentage.percentage)
    if percentage > 100:
      raise ValueError('the plant percentage in this vegetation is over 100%')
    return self._plant_percentages

  @property
  def soil_name(self):
    """
    Get soil name
    :return: string
    """
    return self._soil_name

  @property
  def soil_roughness(self):
    """
    Get soil roughness
    :return: float
    """
    return self._soil_roughness

  @property
  def dry_soil_conductivity(self):
    """
    Get soil dry conductivity in W/mK
    :return: float
    """
    return self._dry_soil_conductivity

  @property
  def dry_soil_density(self):
    """
    Get soil dry density in kg/m3
    :return: float
    """
    return self._dry_soil_density

  @property
  def dry_soil_specific_heat(self):
    """
    Get soil dry specific heat in J/kgK
    :return: float
    """
    return self._dry_soil_specific_heat

  @property
  def soil_thermal_absorptance(self):
    """
    Get soil thermal absortance
    :return: float
    """
    return self._soil_thermal_absorptance

  @property
  def soil_solar_absorptance(self):
    """
    Get soil solar absortance
    :return: float
    """
    return self._soil_solar_absorptance

  @property
  def soil_visible_absorptance(self):
    """
    Get soil visible absortance
    :return: float
    """
    return self._soil_visible_absorptance

  @property
  def soil_saturation_volumetric_moisture_content(self):
    """
    Get soil saturation volumetric moisture content
    :return: float
    """
    return self._soil_saturation_volumetric_moisture_content

  @property
  def soil_residual_volumetric_moisture_content(self):
    """
    Get soil residual volumetric moisture content
    :return: float
    """
    return self._soil_residual_volumetric_moisture_content

  @property
  def soil_initial_volumetric_moisture_content(self):
    """
    Get soil initial volumetric moisture content
    :return: float
    """
    return self._soil_initial_volumetric_moisture_content

  def to_dictionary(self):
    """Class content to dictionary"""
    _plants = []
    for _plant in self.plant_percentages:
      _plants.append(_plant.to_dictionary())
    content = {'Archetype': {'name': self.name,
                             'category': self.category,
                             'air gap thickness [m]': self.air_gap,
                             'soil thickness [m]': self.soil_thickness,
                             'soil name': self.soil_name,
#                             'soil roughness': self.soil_roughness,   # todo: this line prints value=2????
                             'dry soil conductivity [W/m2K]': self.dry_soil_conductivity,
                             'dry soil density [kg/m3]': self.dry_soil_density,
                             'dry soil specific heat [J/kgK]': self.dry_soil_specific_heat,
                             'soil thermal absorptance': self.soil_thermal_absorptance,
                             'soil solar absorptance': self.soil_solar_absorptance,
                             'soil visible absorptance': self.soil_visible_absorptance,
                             'soil saturation volumetric moisture content [units??]': self.soil_saturation_volumetric_moisture_content,
                             'soil residual volumetric moisture content [units??]': self.soil_residual_volumetric_moisture_content,
                             'plants': _plants
                             }
               }

    return content
