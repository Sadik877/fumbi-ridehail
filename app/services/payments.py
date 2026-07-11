"""
Payment provider abstraction.

Flutterwave and Paystack both require a live merchant account and API keys
that only the business owner can obtain — nothing here can fabricate a
working integration without them. What this module DOES provide is the
real, ready-to-use client code: point FLUTTERWAVE_SECRET_KEY /
PAYSTACK_SECRET_KEY at real keys (env vars, see .env.example) and these
functions work against the providers' actual REST APIs with no further
code changes.

Wallet and cash payments are fully functional right now since they don't
depend on a third party — see app/services/wallet.py.
"""
import requests
from flask import current_app


class PaymentError(Exception):
    pass


def _require_key(key_name: str) -> str:
    key = current_app.config.get(key_name)
    if not key:
        raise PaymentError(
            f"{key_name} is not configured. Add it to your environment variables "
            f"to enable this payment provider."
        )
    return key


def initiate_flutterwave_payment(amount, currency, email, tx_ref, redirect_url):
    """Creates a Flutterwave Standard payment link. Docs:
    https://developer.flutterwave.com/docs/collect-payments/standard"""
    secret_key = _require_key("FLUTTERWAVE_SECRET_KEY")
    resp = requests.post(
        "https://api.flutterwave.com/v3/payments",
        headers={"Authorization": f"Bearer {secret_key}"},
        json={
            "tx_ref": tx_ref,
            "amount": str(amount),
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {"email": email},
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "success":
        raise PaymentError(data.get("message", "Flutterwave payment initiation failed"))
    return data["data"]["link"]


def verify_flutterwave_payment(transaction_id: str):
    secret_key = _require_key("FLUTTERWAVE_SECRET_KEY")
    resp = requests.get(
        f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
        headers={"Authorization": f"Bearer {secret_key}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def initiate_paystack_payment(amount_kobo, email, reference, callback_url):
    """Docs: https://paystack.com/docs/payments/accept-payments"""
    secret_key = _require_key("PAYSTACK_SECRET_KEY")
    resp = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers={"Authorization": f"Bearer {secret_key}"},
        json={
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": callback_url,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("status"):
        raise PaymentError(data.get("message", "Paystack payment initiation failed"))
    return data["data"]["authorization_url"]


def verify_paystack_payment(reference: str):
    secret_key = _require_key("PAYSTACK_SECRET_KEY")
    resp = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {secret_key}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
