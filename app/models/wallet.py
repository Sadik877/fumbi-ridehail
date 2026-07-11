import enum
import secrets
from datetime import datetime

from app.extensions import db


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionProvider(str, enum.Enum):
    WALLET = "wallet"
    CASH = "cash"
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    balance = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    pending_balance = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    currency = db.Column(db.String(3), default="NGN", nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = db.relationship(
        "Transaction", backref="wallet", lazy="dynamic", cascade="all, delete-orphan",
        order_by="Transaction.created_at.desc()",
    )


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False)
    reference = db.Column(db.String(48), unique=True, default=lambda: f"TXN-{secrets.token_hex(6).upper()}")

    type = db.Column(db.Enum(TransactionType), nullable=False)
    provider = db.Column(db.Enum(TransactionProvider), nullable=False, default=TransactionProvider.WALLET)
    status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="NGN", nullable=False)
    description = db.Column(db.String(255))
    provider_reference = db.Column(db.String(120))  # Flutterwave/Paystack tx ref for reconciliation

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
