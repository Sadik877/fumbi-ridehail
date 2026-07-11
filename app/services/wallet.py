from decimal import Decimal

from app.extensions import db
from app.models import Transaction, TransactionType, TransactionStatus, TransactionProvider


class InsufficientFundsError(Exception):
    pass


def credit_wallet(wallet, amount, provider: TransactionProvider, description: str, provider_reference=None):
    amount = Decimal(str(amount))
    wallet.balance = (wallet.balance or Decimal("0")) + amount
    txn = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.CREDIT,
        provider=provider,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        currency=wallet.currency,
        description=description,
        provider_reference=provider_reference,
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def debit_wallet(wallet, amount, description: str, provider: TransactionProvider = TransactionProvider.WALLET):
    amount = Decimal(str(amount))
    if (wallet.balance or Decimal("0")) < amount:
        raise InsufficientFundsError("Wallet balance is too low for this transaction.")
    wallet.balance -= amount
    txn = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.DEBIT,
        provider=provider,
        status=TransactionStatus.COMPLETED,
        amount=amount,
        currency=wallet.currency,
        description=description,
    )
    db.session.add(txn)
    db.session.commit()
    return txn
