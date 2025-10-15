#   
#   Imandra Bank
#
#   account.py
#

from currency import Currency
from transaction import DebitTransaction, CreditTransaction, Transaction

class Account:
  """ Account class to represent a bank account """

  LIABILITY = 0
  ASSET = 1

  def __init__(self, customer: str, name: str, currency: int, account_type : int, account_number: str, starting_balance: float = 0.0):
    """ Initialize an account with account number and balance """

    self._account_type  = account_type      # type of account (liability or asset)    
    self._customer      = customer          # customer name
    self._currency      = currency          # currency of the account
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

  def apply_transaction(self, transaction):
    """ Add a transaction to the account """

    # Note: if the "from_account" is this account, then we keep the type of transaction as is
    # if, instead, the "to_account" is this account, then we reverse the type of transaction

    if isinstance(transaction, DebitTransaction):
      if transaction._to_account != self._number:
        trans_type = Transaction.CREDIT
      else:
        trans_type = Transaction.DEBIT

    elif isinstance(transaction, CreditTransaction):
      if transaction._to_account != self._number:
        trans_type = Transaction.DEBIT
      else:
        trans_type = Transaction.CREDIT
        
    if trans_type == Transaction.DEBIT:
      if self._account_type ==  Account.ASSET:
        self._balance += transaction._amount
      elif self._account_type == Account.LIABILITY:
        if self._balance >= transaction._amount:
          self._balance -= transaction._amount
        else:
          raise ValueError("Insufficient balance for debit transaction")

    elif trans_type == Transaction.CREDIT:
      if self._account_type == Account.LIABILITY:
        self._balance += transaction._amount

      elif self._account_type == Account.ASSET:
        if self._balance >= transaction._amount:
          self._balance -= transaction._amount
        else:
          raise ValueError("Insufficient balance for credit transaction")
    
    else:
      raise ValueError("Invalid transaction type")
    
    self._transactions.append(transaction)

  def __repr__(self):
      """ String representation of the account """

      list_transactions = "\n".join(map(str, self._transactions))

      return f"""
      Account Details:
      - Customer: {self.customer()}
      - Name: {self.name()}
      - Account Number: {self.number()}
      - Balance: {self.balance()}
      - Transactions: [\n{list_transactions}\n]
"""

if __name__ == "__main__":
    
    acc = Account("Denis", "Checking Account", Currency.USD, Account.ASSET, "1234567890", 0.0)
    print (acc)

    acc.apply_transaction (DebitTransaction("1234567891", "1234567890", 100.0))
    print(acc)

    acc.apply_transaction (CreditTransaction("1234567891", "1234567890", 50.0))
    print(acc)

    acc.apply_transaction (DebitTransaction("1234567890", "1234567891", 30.0))
    print(acc)

    acc.apply_transaction (CreditTransaction("1234567891", "1234567890", 20.0))