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

  def __init__(self, curve_type, dependant_variable, parameters, coefficients):
    self._curve_type = curve_type
    self._dependant_variable = dependant_variable
    self._parameters = parameters
    self._coefficients = coefficients

  @property
  def curve_type(self):
    """
    The type of the fit function from the following
    Linear =>>> y = a + b*x
    Exponential =>>> y = a*(b**x)
    Second degree polynomial =>>> y = a + b*x + c*(x**2)
    Power =>>> y = a*(x**b)
    Bi-Quadratic =>>> y = a + b*x + c*(x**2) + d*z + e*(z**2) + f*x*z

    Get the type of function from ['linear', 'exponential', 'second degree polynomial', 'power', 'bi-quadratic']
    :return: string
    """
    return self._curve_type

  @property
  def dependant_variable(self):
    """
    y (e.g. COP in COP = a*source temperature**2 + b*source temperature + c*source temperature*supply temperature +
    d*supply temperature + e*supply temperature**2 + f)
    """
    return self._dependant_variable

  @property
  def parameters(self):
    """
    Get the list of parameters involved in fitting process as ['x', 'z'] (e.g. [source temperature, supply temperature]
    in COP=)
    :return: string
    """
    return self._parameters

  @property
  def coefficients(self):
    """
    Get the coefficients of the functions as list of ['a', 'b', 'c', 'd', 'e', 'f']
    :return: [coefficients]
    """
    return self._coefficients

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Parameter Function': {
      'curve type': self.curve_type,
      'dependant variable': self.dependant_variable,
      'parameter(s)': self.parameters,
      'coefficients': self.coefficients,
    }
    }
    return content
