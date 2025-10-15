#
#   Imandra Bank
#   
#   currency.py
#


class Currency:
   EUR = 1
   USD = 2
   GBP = 3
   JPY = 4
   CNY = 5
   INR = 6
   AUD = 7
   CAD = 8
   CHF = 9
   NZD = 10

class CurrencyPairs:
  """ CurrencyPairs class to represent a collection of currency pairs """

  def __init__ (self, pairs):    
    """ Initialize with a dictionary of currency pairs """

    self._pairs = pairs

  def convert(self, from_currency: int, to_currency: int, amount: float) -> float:
    """ Convert an amount from one currency to another """

    if from_currency == to_currency:
      return amount

    pair_key = (from_currency.name, to_currency.name)
    if pair_key not in self._pairs:
      raise ValueError(f"Currency pair {pair_key} not found")

    rate = self._pairs[pair_key]
    return amount * rate

  def __repr__(self):
    """ String representation of the currency pairs """
    return ""

if __name__ == "__main__":

  rates = {
    (CurrencySymbol.EUR, CurrencySymbol.USD): 1.1,
    (CurrencySymbol.USD, CurrencySymbol.EUR): 0.9,
    (CurrencySymbol.GBP, CurrencySymbol.USD): 1.3,
    (CurrencySymbol.USD, CurrencySymbol.GBP): 0.77,
    (CurrencySymbol.JPY, CurrencySymbol.USD): 0.009,
    (CurrencySymbol.USD, CurrencySymbol.JPY): 110.0,
    (CurrencySymbol.CNY, CurrencySymbol.USD): 0.15,
    (CurrencySymbol.USD, CurrencySymbol.CNY): 6.5,
    (CurrencySymbol.INR, CurrencySymbol.USD): 0.013,
    (CurrencySymbol.USD, CurrencySymbol.INR): 75.0,
    (CurrencySymbol.AUD, CurrencySymbol.USD): 0.7,
    (CurrencySymbol.USD, CurrencySymbol.AUD): 1.4,
    (CurrencySymbol.CAD, CurrencySymbol.USD): 0.8,
    (CurrencySymbol.USD, CurrencySymbol.CAD): 1.25,
    (CurrencySymbol.CHF, CurrencySymbol.USD): 1.05,
    (CurrencySymbol.USD, CurrencySymbol.CHF): 0.95,
    (CurrencySymbol.NZD, CurrencySymbol.USD): 0.65,
    (CurrencySymbol.USD, CurrencySymbol.NZD): 1.54
  }

  pairs = CurrencyPairs(rates)

  pairs.convert(CurrencySymbol.EUR, CurrencySymbol.USD, 100)  # Should return 110.0
  pairs.convert(CurrencySymbol.USD, CurrencySymbol.EUR, 100)  # Should return 90.0
  pairs.convert(CurrencySymbol.GBP, CurrencySymbol.USD, 100)  # Should return 130.0
  pairs.convert(CurrencySymbol.USD, CurrencySymbol.GBP, 100)  # Should return 77.0
  pairs.convert(CurrencySymbol.JPY, CurrencySymbol.USD, 100)  # Should return 0.9
  pairs.convert(CurrencySymbol.USD, CurrencySymbol.JPY, 100)  # Should return 11000.0