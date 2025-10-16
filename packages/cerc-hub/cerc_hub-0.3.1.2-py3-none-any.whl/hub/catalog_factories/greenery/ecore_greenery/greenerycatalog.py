"""Definition of meta model 'greenerycatalog'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'greenerycatalog'
nsURI = 'http://ca.concordia/greenerycatalog'
nsPrefix = 'greenery'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)
Management = EEnum('Management', literals=['Intensive', 'Extensive', 'SemiIntensive', 'NA'])

Roughness = EEnum('Roughness', literals=['VeryRough', 'Rough',
                                         'MediumRough', 'MediumSmooth', 'Smooth', 'VerySmooth'])


class Soil(EObject, metaclass=MetaEClass):

  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  roughness = EAttribute(eType=Roughness, unique=True, derived=False,
                         changeable=True, default_value=Roughness.MediumRough)
  conductivityOfDrySoil = EAttribute(
    eType=EString, unique=True, derived=False, changeable=True, default_value='1.0 W/(m*K)')
  densityOfDrySoil = EAttribute(eType=EString, unique=True, derived=False,
                                changeable=True, default_value='1100 kg/m³')
  specificHeatOfDrySoil = EAttribute(
    eType=EString, unique=True, derived=False, changeable=True, default_value='1200 J/(kg*K)')
  thermalAbsorptance = EAttribute(eType=EString, unique=True,
                                  derived=False, changeable=True, default_value='0.9')
  solarAbsorptance = EAttribute(eType=EString, unique=True,
                                derived=False, changeable=True, default_value='0.7')
  visibleAbsorptance = EAttribute(eType=EString, unique=True,
                                  derived=False, changeable=True, default_value='0.75')
  saturationVolumetricMoistureContent = EAttribute(
    eType=EString, unique=True, derived=False, changeable=True, default_value='0.0')
  residualVolumetricMoistureContent = EAttribute(
    eType=EString, unique=True, derived=False, changeable=True, default_value='0.05')
  initialVolumetricMoistureContent = EAttribute(
    eType=EString, unique=True, derived=False, changeable=True, default_value='0.1')

  def __init__(self, *, name=None, roughness=None, conductivityOfDrySoil=None, densityOfDrySoil=None, specificHeatOfDrySoil=None, thermalAbsorptance=None, solarAbsorptance=None, visibleAbsorptance=None, saturationVolumetricMoistureContent=None, residualVolumetricMoistureContent=None, initialVolumetricMoistureContent=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name

    if roughness is not None:
      self.roughness = roughness

    if conductivityOfDrySoil is not None:
      self.conductivityOfDrySoil = conductivityOfDrySoil

    if densityOfDrySoil is not None:
      self.densityOfDrySoil = densityOfDrySoil

    if specificHeatOfDrySoil is not None:
      self.specificHeatOfDrySoil = specificHeatOfDrySoil

    if thermalAbsorptance is not None:
      self.thermalAbsorptance = thermalAbsorptance

    if solarAbsorptance is not None:
      self.solarAbsorptance = solarAbsorptance

    if visibleAbsorptance is not None:
      self.visibleAbsorptance = visibleAbsorptance

    if saturationVolumetricMoistureContent is not None:
      self.saturationVolumetricMoistureContent = saturationVolumetricMoistureContent

    if residualVolumetricMoistureContent is not None:
      self.residualVolumetricMoistureContent = residualVolumetricMoistureContent

    if initialVolumetricMoistureContent is not None:
      self.initialVolumetricMoistureContent = initialVolumetricMoistureContent


class Plant(EObject, metaclass=MetaEClass):

  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  height = EAttribute(eType=EString, unique=True, derived=False,
                      changeable=True, default_value='0.1 m')
  leafAreaIndex = EAttribute(eType=EString, unique=True, derived=False,
                             changeable=True, default_value='2.5')
  leafReflectivity = EAttribute(eType=EString, unique=True,
                                derived=False, changeable=True, default_value='0.1')
  leafEmissivity = EAttribute(eType=EString, unique=True, derived=False,
                              changeable=True, default_value='0.9')
  minimalStomatalResistance = EAttribute(
    eType=EString, unique=True, derived=False, changeable=True, default_value='100.0  s/m')
  co2Sequestration = EAttribute(eType=EString, unique=True, derived=False,
                                changeable=True, default_value='kgCO₂eq')
  growsOn = EReference(ordered=True, unique=True, containment=False, derived=False, upper=-1)

  def __init__(self, *, name=None, height=None, leafAreaIndex=None, leafReflectivity=None, leafEmissivity=None, minimalStomatalResistance=None, growsOn=None, co2Sequestration=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name

    if height is not None:
      self.height = height

    if leafAreaIndex is not None:
      self.leafAreaIndex = leafAreaIndex

    if leafReflectivity is not None:
      self.leafReflectivity = leafReflectivity

    if leafEmissivity is not None:
      self.leafEmissivity = leafEmissivity

    if minimalStomatalResistance is not None:
      self.minimalStomatalResistance = minimalStomatalResistance

    if co2Sequestration is not None:
      self.co2Sequestration = co2Sequestration

    if growsOn:
      self.growsOn.extend(growsOn)


class SupportEnvelope(EObject, metaclass=MetaEClass):

  roughness = EAttribute(eType=Roughness, unique=True, derived=False,
                         changeable=True, default_value=Roughness.MediumRough)
  solarAbsorptance = EAttribute(eType=EDouble, unique=True,
                                derived=False, changeable=True, default_value=0.0)
  conductivity = EAttribute(eType=EDouble, unique=True, derived=False,
                            changeable=True, default_value=0.0)
  visibleAbsorptance = EAttribute(eType=EDouble, unique=True,
                                  derived=False, changeable=True, default_value=0.0)
  specificHeat = EAttribute(eType=EDouble, unique=True, derived=False,
                            changeable=True, default_value=0.0)
  density = EAttribute(eType=EDouble, unique=True, derived=False,
                       changeable=True, default_value=0.0)
  thermalAbsorptance = EAttribute(eType=EDouble, unique=True,
                                  derived=False, changeable=True, default_value=0.0)

  def __init__(self, *, roughness=None, solarAbsorptance=None, conductivity=None, visibleAbsorptance=None, specificHeat=None, density=None, thermalAbsorptance=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if roughness is not None:
      self.roughness = roughness

    if solarAbsorptance is not None:
      self.solarAbsorptance = solarAbsorptance

    if conductivity is not None:
      self.conductivity = conductivity

    if visibleAbsorptance is not None:
      self.visibleAbsorptance = visibleAbsorptance

    if specificHeat is not None:
      self.specificHeat = specificHeat

    if density is not None:
      self.density = density

    if thermalAbsorptance is not None:
      self.thermalAbsorptance = thermalAbsorptance


class GreeneryCatalog(EObject, metaclass=MetaEClass):

  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  description = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  source = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  plantCategories = EReference(ordered=True, unique=True,
                               containment=True, derived=False, upper=-1)
  vegetationCategories = EReference(ordered=True, unique=True,
                                    containment=True, derived=False, upper=-1)
  soils = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

  def __init__(self, *, name=None, description=None, source=None, plantCategories=None, vegetationCategories=None, soils=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name

    if description is not None:
      self.description = description

    if source is not None:
      self.source = source

    if plantCategories:
      self.plantCategories.extend(plantCategories)

    if vegetationCategories:
      self.vegetationCategories.extend(vegetationCategories)

    if soils:
      self.soils.extend(soils)


class PlantCategory(EObject, metaclass=MetaEClass):
  """Excluding (that is non-overlapping) categories like Trees, Hedeges, Grasses that help users finding a specific biol. plant species."""
  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  plants = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

  def __init__(self, *, name=None, plants=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name

    if plants:
      self.plants.extend(plants)


class IrrigationSchedule(EObject, metaclass=MetaEClass):

  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)

  def __init__(self, *, name=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name


class Vegetation(EObject, metaclass=MetaEClass):
  """Plant life or total plant cover (as of an area)"""
  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  thicknessOfSoil = EAttribute(eType=EString, unique=True, derived=False,
                               changeable=True, default_value='20 cm')
  management = EAttribute(eType=Management, unique=True, derived=False,
                          changeable=True, default_value=Management.NA)
  airGap = EAttribute(eType=EString, unique=True, derived=False,
                      changeable=True, default_value='0.0 cm')
  soil = EReference(ordered=True, unique=True, containment=False, derived=False)
  plants = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

  def __init__(self, *, name=None, thicknessOfSoil=None, soil=None, plants=None, management=None, airGap=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name

    if thicknessOfSoil is not None:
      self.thicknessOfSoil = thicknessOfSoil

    if management is not None:
      self.management = management

    if airGap is not None:
      self.airGap = airGap

    if soil is not None:
      self.soil = soil

    if plants:
      self.plants.extend(plants)


class VegetationCategory(EObject, metaclass=MetaEClass):
  """Excluding (that is non-overlapping) categories to help users finding a specific vegetation template."""
  name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
  vegetationTemplates = EReference(ordered=True, unique=True,
                                   containment=True, derived=False, upper=-1)

  def __init__(self, *, vegetationTemplates=None, name=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if name is not None:
      self.name = name

    if vegetationTemplates:
      self.vegetationTemplates.extend(vegetationTemplates)


class PlantPercentage(EObject, metaclass=MetaEClass):

  percentage = EAttribute(eType=EString, unique=True, derived=False,
                          changeable=True, default_value='100')
  plant = EReference(ordered=True, unique=True, containment=False, derived=False)

  def __init__(self, *, percentage=None, plant=None):
    # if kwargs:
    #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

    super().__init__()

    if percentage is not None:
      self.percentage = percentage

    if plant is not None:
      self.plant = plant
