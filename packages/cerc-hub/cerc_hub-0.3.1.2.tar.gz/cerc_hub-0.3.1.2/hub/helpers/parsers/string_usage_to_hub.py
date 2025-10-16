
class StringUsageToHub:
  """
  Eilat function to hub function class
  """

  def parse(self, usages) -> list[dict]:
    """
    Parse usage string in form residential-80_commercial-20
    :usages: str 
    :return: {}
    """

    parsed_usages = []
    for usage in usages.split('_'):
      usage_dict = {"usage": str(usage.split('-')[0]), "ratio": float(usage.split('-')[1])/100}
      parsed_usages.append(usage_dict)

    return parsed_usages
