#
#   Imandra Bank
#
#   ledger.py
#

from asset import Asset
from liability import Liability
from currency import Currency, CurrencyPairs
from account import Account

class BalanceSheetReport:
  """ Class to generate a balance sheet report from the ledger """

  def __init__(self, ledger, tgt_currency: int = Currency.USD):
    """ Initialize the report with a ledger """
    self._ledger = ledger

  def __repr__(self):
    """ Get some summary statistics """

    def convert(account):
      """ Convert the account value to the target currency """
      if account.currency() == Currency.USD:
        return account.balance()
      else:
        return CurrencyPairs().convert(account.currency(), Currency.USD, account.balance())
        
    total_assets = sum(convert(asset) for asset in  self._ledger._assets)
    total_liabilities = sum(convert(liability) for liability in self._ledger._liabilities)

    # Now return the whole thing back to us...
    return {
      "Total Assets": total_assets,
      "Total Liabilities": total_liabilities,
      "Net Assets": total_assets - total_liabilities
    }

class Ledger:
  """ Represents the ledger of a bank, containing assets and liabilities """

  def __init__(self, assets = [], liabilities = []):
    """ Initialize the ledger with empty asset and liability lists """
    self._assets = assets
    self._liabilities = liabilities

  def gen_report(self):
    """ Generate a balance sheet report from the ledger """
    return BalanceSheetReport(self).generate()

  def __repr__(self):
    """ Return a string representation of the ledger """
    asset_list = "\n".join(str(asset) for asset in self._assets)
    liability_list = "\n".join(str(liability) for liability in self._liabilities)

    return f"""
    Ledger:
    Assets: \n{asset_list}

    Liabilities: \n{liability_list}
"""

if __name__ == "__main__":
  
  # !!!! Note: from bank's perspective, customer accounts are liabilities, not assets !!!!
  a, l = [], [] # assets and liabilities

  # let's add some assets to this thing
  l.append( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ))
  l.append( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ))
  l.append( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ))
  l.append( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ))
  l.append( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ))
  l.append( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ))

  # let's now add some liabilities to this thing
  a.append( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ))
  a.append( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ))
  a.append( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ))
  a.append( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ))
  a.append( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ))
  a.append( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ))

  ledger = Ledger(a, l)

  print(BalanceSheetReport(ledger))
