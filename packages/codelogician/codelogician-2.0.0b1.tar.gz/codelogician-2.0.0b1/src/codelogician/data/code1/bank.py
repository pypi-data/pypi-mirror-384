#
#   Imandra Bank
#
#   bank.py
#

from .account import Account
from .asset import Asset
from .currency import Currency
from .ledger import Ledger
from .liability import Liability
from .transaction import Transaction

class Bank:
  """ Bank class to manage transactions """

  def __init__(self):
    """ Initialize the bank with an empty transaction list """
    self._bs = Ledger() # balance sheet
    self._accounts = [] # list of customer accounts

  def add_transaction(self, transaction: Transaction):
    """ Add a transaction to the bank """
    self._transactions.append(transaction)

  def get_transactions(self):
    """ Get all transactions in the bank """
    return self._transactions

  def create_account (self, customer: str, name: str, currency: int, account_type: int, account_number: str, starting_balance: float = 0.0):
    """ Create a new account in the bank """
    account = Account(customer, name, currency, account_type, account_number, starting_balance)
    self._accounts.append(account)
    return account
  
  def process_transaction(self, transaction: Transaction):
    """ Process a transaction and update the balance sheet """

    if isinstance(transaction, Transaction):
      self.add_transaction(transaction)
      # Update the balance sheet based on the transaction type
      if transaction.type == Transaction.DEBIT:
        # Handle debit transaction logic
        pass
      elif transaction.type == Transaction.CREDIT:
        # Handle credit transaction logic
        pass

  def __repr__(self):
    return f"Bank with {len(self._transactions)} transactions"

if __name__ == "__main__":
    # Example usage
    
    bank = Bank()
    bank.add_transaction(Transaction("Deposit", 100))
    bank.add_transaction(Transaction("Withdrawal", 50))
    
    print(bank)
    for transaction in bank.get_transactions():
        print(transaction)
