
class ListUsageToHub:
  """
  Eilat function to hub function class
  """

  def __init__(self, function_dictionary=None):
    self._function_dictionary = function_dictionary

  def _apply_function_dictionary(self, usages):

    function_dictionary = self._function_dictionary

    if function_dictionary is not None:
      for usage in usages:
        if usage['usage'] in function_dictionary:
          usage['usage'] = function_dictionary[usage['usage']]

    return usages
    
  def parse(self, usages) -> list[dict]:
    """
    Get the dictionary
    :return: {}
    """

    usages = [{"usage": str(i["usage"]), "ratio": float(i["ratio"])} for i in usages]

    usages = self._apply_function_dictionary(usages)

    return usages
