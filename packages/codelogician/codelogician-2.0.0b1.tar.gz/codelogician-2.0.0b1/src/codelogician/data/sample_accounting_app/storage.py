from typing import Dict
from .models import Account, Transaction


class InMemoryStorage:
    def __init__(self):
        self.accounts: Dict[int, Account] = {}
        self.transactions: Dict[int, Transaction] = {}

    def add_account(self, account: Account):
        self.accounts[account.id] = account

    def add_transaction(self, txn: Transaction):
        self.transactions[txn.id] = txn
