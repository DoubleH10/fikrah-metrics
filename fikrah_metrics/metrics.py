"""SaaS metrics computation from Stripe data.

Computes: MRR, ARR, NRR, gross churn, expansion, contraction,
new MRR, churned MRR, runway, burn rate, customer count, ARPU.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MonthlySnapshot:
    """Revenue snapshot for a single month."""
    month: str  # "2026-03"
    mrr: float = 0.0
    new_mrr: float = 0.0
    expansion_mrr: float = 0.0
    contraction_mrr: float = 0.0
    churned_mrr: float = 0.0
    active_customers: int = 0
    new_customers: int = 0
    churned_customers: int = 0


@dataclass
class SaaSMetrics:
    """Computed SaaS metrics."""
    # Current
    mrr: float = 0.0
    arr: float = 0.0
    active_subscriptions: int = 0
    total_customers: int = 0
    arpu: float = 0.0

    # Growth
    mrr_growth_rate: float = 0.0  # month-over-month %
    new_mrr: float = 0.0
    expansion_mrr: float = 0.0
    contraction_mrr: float = 0.0
    churned_mrr: float = 0.0

    # Retention
    net_revenue_retention: float = 0.0  # NRR %
    gross_revenue_retention: float = 0.0  # GRR %
    logo_churn_rate: float = 0.0  # customer churn %

    # Runway
    cash_balance: float = 0.0
    monthly_burn: float = 0.0  # estimated from revenue trend
    runway_months: float = 0.0

    # History
    monthly_snapshots: list[MonthlySnapshot] = field(default_factory=list)

    # Meta
    currency: str = "usd"
    computed_at: str = ""


def compute_metrics(
    data: dict[str, Any],
    bank_balance: float | None = None,
    monthly_expenses: float | None = None,
) -> SaaSMetrics:
    """Compute SaaS metrics from Stripe data.

    Args:
        data: Output from fetch_stripe_data()
        bank_balance: Optional manual bank balance for runway calc
        monthly_expenses: Optional monthly expense override for burn rate
    """
    subscriptions = data["subscriptions"]
    invoices = data["invoices"]
    customers = data["customers"]
    balance = data["balance"]

    # ── Current MRR from active subscriptions ────────────────────────
    active_subs = [s for s in subscriptions if s["status"] in ("active", "trialing")]

    mrr = 0.0
    for sub in active_subs:
        for item in sub.get("items", {}).get("data", []):
            plan = item.get("plan", {}) or item.get("price", {})
            amount = (plan.get("amount") or 0) / 100  # cents to dollars
            interval = plan.get("interval", "month")
            interval_count = plan.get("interval_count", 1)

            if interval == "year":
                mrr += amount / (12 * interval_count)
            elif interval == "month":
                mrr += amount / interval_count
            elif interval == "week":
                mrr += amount * 4.33 / interval_count
            elif interval == "day":
                mrr += amount * 30 / interval_count

    arr = mrr * 12
    arpu = mrr / len(active_subs) if active_subs else 0

    # ── Monthly snapshots from invoices ──────────────────────────────
    monthly_revenue: dict[str, float] = defaultdict(float)
    monthly_customers: dict[str, set] = defaultdict(set)

    for inv in invoices:
        if not inv.get("customer"):
            continue
        created = datetime.fromtimestamp(inv["created"], tz=timezone.utc)
        month_key = created.strftime("%Y-%m")
        amount = (inv.get("amount_paid") or 0) / 100
        monthly_revenue[month_key] += amount
        monthly_customers[month_key].add(inv["customer"])

    sorted_months = sorted(monthly_revenue.keys())

    snapshots: list[MonthlySnapshot] = []
    prev_customers: set[str] = set()
    prev_mrr: float = 0.0

    for month in sorted_months:
        current_customers = monthly_customers[month]
        revenue = monthly_revenue[month]

        new_customers = current_customers - prev_customers
        churned = prev_customers - current_customers
        retained = current_customers & prev_customers

        # Approximate MRR breakdown from invoice data
        snap = MonthlySnapshot(
            month=month,
            mrr=revenue,
            active_customers=len(current_customers),
            new_customers=len(new_customers),
            churned_customers=len(churned),
        )

        if prev_mrr > 0 and len(sorted_months) > 1:
            # Estimate new vs expansion vs churn MRR
            snap.new_mrr = max(0, revenue - prev_mrr) if len(new_customers) > 0 else 0
            snap.churned_mrr = max(0, prev_mrr - revenue) if len(churned) > 0 else 0
            if revenue > prev_mrr:
                snap.expansion_mrr = max(0, revenue - prev_mrr - snap.new_mrr)
            else:
                snap.contraction_mrr = max(0, prev_mrr - revenue - snap.churned_mrr)

        snapshots.append(snap)
        prev_customers = current_customers
        prev_mrr = revenue

    # ── Growth metrics ───────────────────────────────────────────────
    mrr_growth = 0.0
    if len(snapshots) >= 2 and snapshots[-2].mrr > 0:
        mrr_growth = (snapshots[-1].mrr - snapshots[-2].mrr) / snapshots[-2].mrr * 100

    latest = snapshots[-1] if snapshots else MonthlySnapshot(month="")

    # ── Retention ────────────────────────────────────────────────────
    nrr = 0.0
    grr = 0.0
    logo_churn = 0.0

    if len(snapshots) >= 2:
        prev = snapshots[-2]
        curr = snapshots[-1]
        if prev.mrr > 0:
            nrr = ((prev.mrr + curr.expansion_mrr - curr.contraction_mrr - curr.churned_mrr) / prev.mrr) * 100
            grr = ((prev.mrr - curr.contraction_mrr - curr.churned_mrr) / prev.mrr) * 100
        if prev.active_customers > 0:
            logo_churn = (curr.churned_customers / prev.active_customers) * 100

    # ── Cash & Runway ────────────────────────────────────────────────
    # Stripe balance
    stripe_balance = 0.0
    for b in balance.get("available", []):
        stripe_balance += b.get("amount", 0) / 100
    for b in balance.get("pending", []):
        stripe_balance += b.get("amount", 0) / 100

    cash = bank_balance if bank_balance is not None else stripe_balance
    burn = monthly_expenses if monthly_expenses is not None else max(0, mrr * 0.8)  # rough estimate
    runway = cash / burn if burn > 0 else float("inf")

    # Currency from balance
    currency = "usd"
    if balance.get("available"):
        currency = balance["available"][0].get("currency", "usd")

    return SaaSMetrics(
        mrr=round(mrr, 2),
        arr=round(arr, 2),
        active_subscriptions=len(active_subs),
        total_customers=len(customers),
        arpu=round(arpu, 2),
        mrr_growth_rate=round(mrr_growth, 1),
        new_mrr=round(latest.new_mrr, 2),
        expansion_mrr=round(latest.expansion_mrr, 2),
        contraction_mrr=round(latest.contraction_mrr, 2),
        churned_mrr=round(latest.churned_mrr, 2),
        net_revenue_retention=round(nrr, 1),
        gross_revenue_retention=round(grr, 1),
        logo_churn_rate=round(logo_churn, 1),
        cash_balance=round(cash, 2),
        monthly_burn=round(burn, 2),
        runway_months=round(runway, 1) if runway != float("inf") else -1,
        monthly_snapshots=snapshots,
        currency=currency,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )
