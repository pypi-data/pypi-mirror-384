#
#   Imandra Bank
#
#   transaction.py
#

from .currency import Currency

class Transaction:
  """ Transaction class to represent a financial transaction """
  DEBIT = 1
  CREDIT = 2

  def __init__(self, trans_type : int, from_account : str, to_account : str, amount: float):
    """ Initialize a transaction with type and amount """

    self._type = trans_type
    self._from_account = from_account
    self._to_account = to_account
    self._amount = amount

  def __repr__(self):
    return f"Transaction(from_account={self._from_account}, to_account={self._to_account} ,amount={self._amount})"

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

  # Example usage
  t1 = Transaction("Deposit", 100.0)
  t2 = Transaction("Withdrawal", 50.0)

  print(t1)
  print(t2)

  # Check equality
  print(t1 == Transaction("Deposit", 100.0))  # True
  print(t1 == t2)  # False

  # Create debit and credit transactions
  debit = DebitTransaction(30.0)
  credit = CreditTransaction(70.0)

  #  Print debit and credit transactions
  print(debit)
  print(credit)
  print(debit == DebitTransaction(30.0))  # True
