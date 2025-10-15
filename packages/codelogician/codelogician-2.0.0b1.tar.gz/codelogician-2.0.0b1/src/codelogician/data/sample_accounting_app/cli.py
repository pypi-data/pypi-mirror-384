from .storage import InMemoryStorage
from .services import AccountingService
from .models import AccountType, Entry


def run_cli():
    storage = InMemoryStorage()
    service = AccountingService(storage)

    # Create accounts
    cash = service.create_account("Cash", AccountType.ASSET)
    revenue = service.create_account("Revenue", AccountType.INCOME)
    expense = service.create_account("Supplies Expense", AccountType.EXPENSE)

    # Post a transaction: Earned $500 revenue (cash increases, revenue increases)
    service.post_transaction(
        "Service revenue",
        [
            Entry(account_id=cash.id, debit=500.0),
            Entry(account_id=revenue.id, credit=500.0),
        ],
    )

    # Post a transaction: Bought supplies $200 (cash decreases, expense increases)
    service.post_transaction(
        "Supplies purchase",
        [
            Entry(account_id=expense.id, debit=200.0),
            Entry(account_id=cash.id, credit=200.0),
        ],
    )

    print("== Account Balances ==")
    for name, balance in service.get_account_balances().items():
        print(f"{name}: {balance:.2f}")

    debits, credits = service.trial_balance()
    print("\n== Trial Balance ==")
    print(f"Debits: {debits:.2f}, Credits: {credits:.2f}")
