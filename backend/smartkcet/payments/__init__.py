"""Razorpay payment gateway integration for SmartKCET Prep.

Payment Gateway: Razorpay
- UPI (QR + ID), Debit/Credit Card (Visa/Mastercard/RuPay)
- Net Banking, Wallets, GPay/PhonePe/Paytm

Security model:
  1. Frontend calls POST /api/payments/create-order → gets Razorpay order_id
  2. Frontend opens Razorpay checkout modal (payment happens on Razorpay)
  3. On success Razorpay calls our webhook POST /api/payments/webhook
  4. Webhook verifies HMAC-SHA256 signature → activates subscription
  5. Subscription is NEVER activated from frontend success callback alone
"""

from .routes import router

__all__ = ["router"]
