#   
#   Imandra Bank
#
#   account.py
#

from .currency import Currency
from .transaction import DebitTransaction, CreditTransaction

class Account:
  """ Account class to represent a bank account """

  LIABILITY = 0
  ASSET = 1

  def __init__(self, customer: str, name: str, currency: int, account_type : int, account_number: str, starting_balance: float = 0.0):
    """ Initialize an account with account number and balance """

    self._account_type  = account_type      # type of account (liability or asset)    
    self._customer      = customer          # customer name
    self._name          = name              # account name
    self._number        = account_number    # account number 
    self._balance       = starting_balance  # current balance
    self._transactions  = []                # list of transactions

  def account_type (self):
    """ Get the type of the account """
    return self._account_type

  def customer(self):
    """ Get the customer associated with the account """
    return self._customer
  
  def name(self):
    """ Get the name of the account """
    return self._name

  def number(self):
    """ Get the account number """
    return self._number

  def currency(self):
    """ Get the currency of the account """
    return self._currency

  def balance(self):
    """ return the current balance of the account """
    return self._balance
  
  def transactions(self):
    """ Get the list of transactions in the account """
    return self._transactions

  def add_transaction(self, transaction):
    """ Add a transaction to the account """

    if isinstance(transaction, DebitTransaction):
      if self._type() ==  Account.ASSET and self._balance >= transaction.amount:
        self._balance -= transaction.amount
      else:
        raise ValueError("Insufficient balance for debit transaction")

    elif isinstance(transaction, CreditTransaction):
      if self._type() == Account.LIABILITY:
        self._balance += transaction.amount
      elif self._type() == Account.ASSET:
        self._balance -= transaction.amount
      else:
        raise ValueError("Invalid account type for credit transaction")
    
    else:
      raise ValueError("Invalid transaction type")

    self._transactions.append(transaction)

    def __repr__(self):
      """ String representation of the account """
      return f"Account(account_number={self.account_number}, balance={self.balance})"

if __name__ == "__main__":
    # Example usage
    account = Account("base_account", "123456789", 1000.0)
