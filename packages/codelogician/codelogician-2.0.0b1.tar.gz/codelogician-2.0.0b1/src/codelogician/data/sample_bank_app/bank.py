#
#   Imandra Bank
#
#   bank.py
#

from account import Account
from asset import Asset
from currency import Currency
from ledger import Ledger
from liability import Liability
from transaction import Transaction, DebitTransaction, CreditTransaction

class Bank:
  """ Bank class to manage transactions """

  def __init__(self):
    """ Initialize the bank with an empty transaction list """
    self._ledger = Ledger() # balance sheet
    self._accounts = [] # list of customer accounts

  def get_transactions(self):
    """ Get all transactions in the bank """
    return self._transactions

  def create_account (self, customer: str, name: str, currency: int, account_type: int, account_number: str, starting_balance: float = 0.0):
    """ Create a new account in the bank """
    account = Account(customer, name, currency, account_type, account_number, starting_balance)
    self._accounts.append(account)
    return account
  
  def add_account (self, acc : Account):
    """ Add an already existing account object """
    self._accounts.append(acc)
  
  def get_account_by_id (self, acc_number):
    """ return account if it exists that matched the ID """

    acc = next (a for a in self._accounts if a.number() == acc_number)

    return acc

  def add_transaction(self, t: Transaction):
    """ Process a transaction and update the balance sheet """

    accOne = self.get_account_by_id ( t.from_account() )
    accTwo = self.get_account_by_id ( t.to_account()   )

    if accOne: accOne.apply_transaction(t)
    if accTwo: accTwo.apply_transaction(t)

  def __repr__(self):
    """ Return a nice representation of the bank """
    
    accountStr = "\n".join(map (str, self._accounts))
    bsStr = str(self._ledger)

    return f"Bank with Accounts: \n{accountStr}\n and Balance Sheet: \n {bsStr}"

if __name__ == "__main__":
    # Example usage
    
    bank = Bank()

    bank.add_account ( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ) )
    bank.add_account ( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ) )
    bank.add_account ( Account( "Jane Doe"  , "Checking Account"  , Currency.USD  , Account.ASSET   , "987654321"   , 1500.0 ) )
    bank.add_account ( Account( "John Doe"  , "Savings Account"   , Currency.USD  , Account.ASSET   , "123456789"   , 1000.0 ) )

    # let's now add some transactions
    bank.add_transaction(DebitTransaction("123456789", "987654321", 100))
    bank.add_transaction(CreditTransaction("987654321", "123456789", 50))

    print (bank)