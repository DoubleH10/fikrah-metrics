"""Stripe API client — fetch subscriptions, invoices, and charges.

Handles pagination automatically. Returns raw data for metrics computation.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import stripe


def fetch_stripe_data(api_key: str, months: int = 13) -> dict[str, Any]:
    """Fetch all data needed for SaaS metrics from Stripe.

    Args:
        api_key: Stripe secret key (sk_live_* or sk_test_*)
        months: How many months of history to fetch (default 13 for YoY)

    Returns:
        Dict with subscriptions, invoices, customers, balance
    """
    stripe.api_key = api_key

    now = int(time.time())
    cutoff = int(datetime(
        datetime.now(timezone.utc).year,
        datetime.now(timezone.utc).month,
        1,
        tzinfo=timezone.utc,
    ).timestamp()) - (months * 30 * 86400)

    # Fetch active subscriptions
    subscriptions = []
    for sub in stripe.Subscription.list(status="all", limit=100).auto_paging_iter():
        subscriptions.append(sub)

    # Fetch invoices (paid, in the time window)
    invoices = []
    for inv in stripe.Invoice.list(
        created={"gte": cutoff},
        status="paid",
        limit=100,
    ).auto_paging_iter():
        invoices.append(inv)

    # Fetch customers
    customers = []
    for cust in stripe.Customer.list(limit=100).auto_paging_iter():
        customers.append(cust)

    # Fetch balance
    balance = stripe.Balance.retrieve()

    return {
        "subscriptions": subscriptions,
        "invoices": invoices,
        "customers": customers,
        "balance": balance,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
