from .models import Account, Transaction, Entry
from .storage import InMemoryStorage


class AccountingService:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage
        self.next_account_id = 1
        self.next_txn_id = 1

    def create_account(self, name: str, type_: str) -> Account:
        account = Account(id=self.next_account_id, name=name, type=type_)
        self.storage.add_account(account)
        self.next_account_id += 1
        return account

    def post_transaction(self, description: str, entries: list[Entry]) -> Transaction:
        txn = Transaction(id=self.next_txn_id, description=description, entries=entries)
        if not txn.is_balanced():
            raise ValueError("Transaction not balanced: debits != credits")

        # Update account balances
        for entry in entries:
            account = self.storage.accounts[entry.account_id]
            account.balance += entry.debit
            account.balance -= entry.credit

        self.storage.add_transaction(txn)
        self.next_txn_id += 1
        return txn

    def get_account_balances(self):
        return {acc.name: acc.balance for acc in self.storage.accounts.values()}

    def trial_balance(self):
        total_debits = 0.0
        total_credits = 0.0
        for acc in self.storage.accounts.values():
            if acc.balance >= 0:
                total_debits += acc.balance
            else:
                total_credits += -acc.balance
        return total_debits, total_credits
