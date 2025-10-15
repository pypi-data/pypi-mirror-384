#
#   Imandra Bank
#
# liability.py
#

from currency import Currency

class LiabilityType:
  """ Enum for liability types """
  LOAN = 0
  MORTGAGE = 1
  CREDIT_CARD = 2
  OTHER = 3

  def to_string(self):
    """ Convert the liability type to a string """
    return {
      self.LOAN: "Loan",
      self.MORTGAGE: "Mortgage",
      self.CREDIT_CARD: "Credit Card",
      self.OTHER: "Other"
    }.get(self, "Unknown")

class Liability:
  """ Liability class to represent a financial liability """

  def __init__(self, amount: float):
    """ Initialize a liability with an amount """
    if amount < 0:
      raise ValueError("Liability amount cannot be negative")
    self.amount = amount

  def __repr__(self):
    return f"Liability(amount={self.amount})"

  def __eq__(self, other):
    if not isinstance(other, Liability):
      return False
    return self.amount == other.amount

  def __hash__(self):
    return hash(self.amount)

  def to_dict(self):
    """ Convert the liability to a dictionary """
    return {"amount": self.amount}

  @staticmethod
  def from_dict(data):
    """ Create a liability from a dictionary """
    return Liability(data['amount'])
    
if __name__ == "__main__":
  
  # Example usage
  liability = Liability(5000.0)
  print(liability)

  # Check equality
  liability2 = Liability(5000.0)
  print(liability == liability2)  # Should print True

  # Convert to dictionary
  liability_dict = liability.to_dict()
  print(liability_dict)  # Should print {'amount': 5000.0}

  # Create from dictionary
  liability_from_dict = Liability.from_dict(liability_dict)
  print(liability_from_dict)  # Should print Liability(amount=5000.0)
