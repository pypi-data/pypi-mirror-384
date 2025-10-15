#
#   Imandra Bank
#
#   ledger.py
#

from .asset import Asset
from .liability import Liability
from .currency import Currency

class BalanceSheetReport:
  """ Class to generate a balance sheet report from the ledger """

  def __init__(self, ledger):
    """ Initialize the report with a ledger """
    self.ledger = ledger

  def generate(self):
    """ Generate the balance sheet report """
    assets = self.ledger._assets
    liabilities = self.ledger._liabilities
    total_assets = sum(asset.value for asset in assets)
    total_liabilities = sum(liability.amount for liability in liabilities)
    
    return {
      "total_assets": total_assets,
      "total_liabilities": total_liabilities,
      "net_worth": total_assets - total_liabilities
    }

class Ledger:
  """ Represents the ledger of a bank, containing assets and liabilities """

  def __init__(self):
    """ Initialize the ledger with empty asset and liability lists """
    self._assets = []
    self._liabilities = []


  def gen_report(self):
    pass

  def __repr__(self):
    """  Return a string representation of the ledger """
    return f"Ledger with {len(self._assets)} assets and {len(self._liabilities)} liabilities"

if __name__ == "__main__":
  
  ledger = Ledger()

  ledger._assets.append(Asset(1000.0))
  ledger._liabilities.append(Liability(500.0))

  report = BalanceSheetReport(ledger)
  print(report.generate())
