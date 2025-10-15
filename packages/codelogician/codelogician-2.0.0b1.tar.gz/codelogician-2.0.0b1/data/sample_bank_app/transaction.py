#
#   Imandra Bank
#
#   transaction.py
#

from currency import Currency

class Transaction:
  """ Transaction class to represent a financial transaction """
  DEBIT, CREDIT = 1, 2

  def __init__(self, trans_type : int, from_account : str, to_account : str, amount: float):
    """ Initialize a transaction with type and amount """

    self._type = trans_type
    self._from_account = from_account
    self._to_account = to_account
    self._amount = amount

  def from_account(self):
    """ return the 'from account' property """
    return self._from_account
  
  def to_account(self):
    """ return the 'to account' property """
    return self._to_account

  def __repr__(self):
    """ """
    return f"Transaction(from_account={self._from_account}, to_account={self._to_account}, amount={self._amount})"

  def __eq__(self, other):
    if not isinstance(other, Transaction):
      return False
    return self.type == other.type and self.amount == other.amount
  def __hash__(self):
    return hash((self.type, self.amount))
  
  def to_dict(self):
    """ Convert the transaction to a dictionary """
    return {
      "type": self.type,
      "amount": self.amount
    }

class DebitTransaction(Transaction):
  """ Debit transaction class for withdrawals """
  def __init__(self, from_account : str, to_account : str, amount: float):
    """ Initialize a debit transaction with amount """
    super().__init__(Transaction.DEBIT, from_account, to_account, amount)

class CreditTransaction(Transaction):
  def __init__(self, from_account : str, to_account : str, amount: float):
    """ Initialize a credit transaction with amount """
    super().__init__(Transaction.CREDIT, from_account ,to_account, amount)

if __name__ == "__main__":

  # Debit transaction
  d = DebitTransaction("123456789", "987654321", 100.0)

  # Credit transaction
  c = CreditTransaction("987654321", "123456789", 100.0)
