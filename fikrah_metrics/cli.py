"""CLI entry point for fikrah-metrics."""
from __future__ import annotations

import json
import os
import sys

import click
from rich.console import Console

from fikrah_metrics.display import THEME


@click.command()
@click.option(
    "--stripe-key", "-k",
    envvar="STRIPE_SECRET_KEY",
    help="Stripe secret key (sk_live_* or sk_test_*). Or set STRIPE_SECRET_KEY env var.",
)
@click.option(
    "--bank-balance", "-b",
    type=float,
    default=None,
    help="Current bank balance for runway calculation (overrides Stripe balance).",
)
@click.option(
    "--monthly-expenses", "-e",
    type=float,
    default=None,
    help="Monthly expenses for burn rate (default: estimate from revenue).",
)
@click.option(
    "--months", "-m",
    type=int,
    default=13,
    help="Months of history to analyze (default: 13 for YoY comparison).",
)
@click.option(
    "--json-output", "-j",
    is_flag=True,
    default=False,
    help="Output raw JSON instead of formatted tables.",
)
@click.option(
    "--test",
    is_flag=True,
    default=False,
    help="Use Stripe test mode key (sk_test_*).",
)
def main(
    stripe_key: str | None,
    bank_balance: float | None,
    monthly_expenses: float | None,
    months: int,
    json_output: bool,
    test: bool,
) -> None:
    """SaaS metrics from your Stripe account.

    One command. ARR, MRR, NRR, churn, runway — everything you need
    for your board deck, investor update, or Monday morning standup.

    \b
    Examples:
        fikrah-metrics --stripe-key sk_live_xxx
        fikrah-metrics -k sk_test_xxx --bank-balance 84000
        fikrah-metrics --json-output > metrics.json
        STRIPE_SECRET_KEY=sk_live_xxx fikrah-metrics
    """
    console = Console(theme=THEME)

    if not stripe_key:
        console.print()
        console.print("  [bold red]Stripe key required[/]")
        console.print()
        console.print("  [dim]Pass --stripe-key or set STRIPE_SECRET_KEY:[/]")
        console.print("    [dim]fikrah-metrics --stripe-key sk_live_xxx[/]")
        console.print("    [dim]export STRIPE_SECRET_KEY=sk_live_xxx[/]")
        console.print()
        sys.exit(1)

    # Validate key format
    if not stripe_key.startswith("sk_"):
        console.print("[bold red]Invalid Stripe key format.[/] Must start with sk_live_ or sk_test_")
        sys.exit(1)

    if test and not stripe_key.startswith("sk_test_"):
        console.print("[bold red]--test flag requires a test key (sk_test_*)[/]")
        sys.exit(1)

    # Fetch data
    console.print()
    with console.status("[dim]Fetching data from Stripe...[/]", spinner="dots"):
        try:
            from fikrah_metrics.stripe_client import fetch_stripe_data
            data = fetch_stripe_data(stripe_key, months=months)
        except Exception as e:
            console.print(f"[bold red]Stripe API error:[/] {e}")
            sys.exit(1)

    # Compute metrics
    with console.status("[dim]Computing metrics...[/]", spinner="dots"):
        from fikrah_metrics.metrics import compute_metrics
        metrics = compute_metrics(
            data,
            bank_balance=bank_balance,
            monthly_expenses=monthly_expenses,
        )

    # Output
    if json_output:
        from dataclasses import asdict
        output = asdict(metrics)
        # Remove snapshots for cleaner JSON (optional)
        output["monthly_snapshots"] = [
            {"month": s["month"], "mrr": s["mrr"], "active_customers": s["active_customers"]}
            for s in output["monthly_snapshots"]
        ]
        print(json.dumps(output, indent=2, default=str))
    else:
        from fikrah_metrics.display import display_metrics
        display_metrics(metrics, console=console)


if __name__ == "__main__":
    main()
