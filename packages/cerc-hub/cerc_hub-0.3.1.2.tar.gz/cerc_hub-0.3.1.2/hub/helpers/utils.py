"""
Constant module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Peter Yefi peteryefi@gmail.com
"""
import logging


def validate_import_export_type(cls_name: type, handler: str):
  """
  Retrieves all the function names in a class which are property types (decoration)
  and normal functions
  :param cls_name: the class name
  :param handler: import export handler
  :return: None
  """
  functions = [
    function[1:] for function in dir(cls_name)
    if (
           isinstance(getattr(cls_name, function), property) or callable(getattr(cls_name, function))
       ) and function in cls_name.__dict__ and function[0] == '_' and function != '__init__']

  if handler.lower() not in functions:
    error_message = f'Wrong import type [{handler}]. Valid functions include {functions}'
    logging.error(error_message)
    raise ValueError(error_message)
