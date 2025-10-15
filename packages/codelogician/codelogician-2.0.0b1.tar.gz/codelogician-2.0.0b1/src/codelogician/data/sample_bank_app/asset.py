#
#   Imandra Bank
#
#   asset.py
#

from currency import Currency

class AssetType:
  """ Enum for asset types """
  CASH = 0
  STOCK = 1
  BOND = 2
  REAL_ESTATE = 3
  OTHER = 4

  def to_string(self):
    """ Convert the asset type to a string """
    return {
      self.CASH: "Cash",
      self.STOCK: "Stock",
      self.BOND: "Bond",
      self.REAL_ESTATE: "Real Estate",
      self.OTHER: "Other"
    }.get(self, "Unknown")

class Asset:
  """ Asset class to represent a financial asset """

  def __init__(self, name : str, asset_type : int, value: float):
    """ Initialize an asset with a value """
    if value < 0:
      raise ValueError("Asset value cannot be negative")
    self._value = value
    self._type = asset_type
    self._name = name

  def __repr__(self):
    return f"Asset(name={self._name}, value={self.value})"

  def __eq__(self, other):
    if not isinstance(other, Asset):
      return False
    return self.value == other.value

  def __hash__(self):
    return hash(self.value)

  def to_dict(self):
    """ Convert the asset to a dictionary """
    return {"value": self.value}

  @staticmethod
  def from_dict(data):
    """ Create an asset from a dictionary """
    return Asset(data['value'])

if __name__ == "__main__":
  # Example usage
  asset = Asset(1000.0)
  print(asset)

  # Convert to dictionary
  asset_dict = asset.to_dict()
  print(asset_dict)

  # Create from dictionary
  new_asset = Asset.from_dict(asset_dict)
  print(new_asset)
