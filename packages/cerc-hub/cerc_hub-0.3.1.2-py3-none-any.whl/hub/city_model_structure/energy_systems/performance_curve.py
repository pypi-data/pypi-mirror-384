"""
Energy System catalog heat generation system
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from __future__ import annotations


class PerformanceCurves:
  """
  Parameter function class
  """

  def __init__(self):
    self._curve_type = None
    self._dependant_variable = None
    self._parameters = None
    self._coefficients = None

  @property
  def curve_type(self):
    """
    Get the type of the fit function from the following
    Linear =>>> y = a + b*x
    Exponential =>>> y = a*(b**x)
    Second degree polynomial =>>> y = a + b*x + c*(x**2)
    Power =>>> y = a*(x**b)
    Bi-Quadratic =>>> y = a + b*x + c*(x**2) + d*z + e*(z**2) + f*x*z

    Get the type of function from ['linear', 'exponential', 'second degree polynomial', 'power', 'bi-quadratic']
    :return: string
    """

    return self._curve_type

  @curve_type.setter
  def curve_type(self, value):
    """
    Set the type of the fit function from the following
    Linear =>>> y = a + b*x
    Exponential =>>> y = a*(b**x)
    Second degree polynomial =>>> y = a + b*x + c*(x**2)
    Power =>>> y = a*(x**b)
    Bi-Quadratic =>>> y = a + b*x + c*(x**2) + d*z + e*(z**2) + f*x*z

    Get the type of function from ['linear', 'exponential', 'second degree polynomial', 'power', 'bi-quadratic']
    :return: string
    """
    self._curve_type = value

  @property
  def dependant_variable(self):
    """
    Get y (e.g. COP in COP = a*source temperature**2 + b*source temperature + c*source temperature*supply temperature +
    d*supply temperature + e*supply temperature**2 + f)
    """
    return self._dependant_variable

  @dependant_variable.setter
  def dependant_variable(self, value):
    """
    Set y (e.g. COP in COP = a*source temperature**2 + b*source temperature + c*source temperature*supply temperature +
    d*supply temperature + e*supply temperature**2 + f)
    """
    self._dependant_variable = value

  @property
  def parameters(self):
    """
    Get the list of parameters involved in fitting process as ['x', 'z'] (e.g. [source temperature, supply temperature]
    in COP= *source temperature**2 + b*source temperature + c*source temperature*supply temperature +
    d*supply temperature + e*supply temperature**2 + f)
    :return: string
    """
    return self._parameters

  @parameters.setter
  def parameters(self, value):
    """
    Set the list of parameters involved in fitting process as ['x', 'z'] (e.g. [source temperature, supply temperature]
    in COP= *source temperature**2 + b*source temperature + c*source temperature*supply temperature +
    d*supply temperature + e*supply temperature**2 + f)
    :return: string
    """
    self._parameters = value

  @property
  def coefficients(self):
    """
    Get the coefficients of the functions as list of ['a', 'b', 'c', 'd', 'e', 'f']
    :return: [coefficients]
    """
    return self._coefficients

  @coefficients.setter
  def coefficients(self, value):
    """
    Set the coefficients of the functions as list of ['a', 'b', 'c', 'd', 'e', 'f']
    :return: [coefficients]
    """
    self._coefficients = value
