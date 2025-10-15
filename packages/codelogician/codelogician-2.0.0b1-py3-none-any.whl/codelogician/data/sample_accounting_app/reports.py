from .models import AccountType
from .storage import InMemoryStorage


class Reports:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def income_statement(self):
        revenues = sum(
            acc.balance for acc in self.storage.accounts.values()
            if acc.type == AccountType.INCOME
        )
        expenses = sum(
            acc.balance for acc in self.storage.accounts.values()
            if acc.type == AccountType.EXPENSE
        )
        net_income = revenues - expenses
        return {"revenues": revenues, "expenses": expenses, "net_income": net_income}

    def balance_sheet(self):
        assets = sum(
            acc.balance for acc in self.storage.accounts.values()
            if acc.type == AccountType.ASSET
        )
        liabilities = sum(
            acc.balance for acc in self.storage.accounts.values()
            if acc.type == AccountType.LIABILITY
        )
        equity = sum(
            acc.balance for acc in self.storage.accounts.values()
            if acc.type == AccountType.EQUITY
        )

        # Include retained earnings (net income)
        income_stmt = self.income_statement()
        retained_earnings = income_stmt["net_income"]

        total_liab_equity = liabilities + equity + retained_earnings
        return {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "retained_earnings": retained_earnings,
            "liabilities_plus_equity": total_liab_equity,
        }
