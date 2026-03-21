"""CLI entry point for fikrah-metrics — interactive, beautiful, one command."""
from __future__ import annotations

import json
import os
import sys

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.theme import Theme

THEME = Theme({
    "fikrah.brand": "bold #D1E95C",
    "fikrah.accent": "#D1E95C",
    "fikrah.dim": "#6b7c6e",
    "fikrah.green": "#22C55E",
    "fikrah.red": "#EF4444",
    "fikrah.sage": "#E8F0ED",
    "fikrah.error": "bold red",
    "fikrah.success": "bold #D1E95C",
})

BANNER = """\
[#D1E95C]  ╭────────────────────────────────────╮[/]
[#c8e64a]  │                                    │[/]
[#b0e14d]  │    [bold #D1E95C]f i k r a h[/]   [dim]metrics[/dim]    │[/]
[#99dd50]  │                                    │[/]
[#81d853]  ╰────────────────────────────────────╯[/]
"""


@click.command()
@click.option(
    "--stripe-key", "-k",
    envvar="STRIPE_SECRET_KEY",
    default=None,
    help="Stripe secret key. If not provided, you'll be prompted.",
)
@click.option(
    "--bank-balance", "-b",
    type=float,
    default=None,
    help="Bank balance for runway calculation (overrides Stripe balance).",
)
@click.option(
    "--monthly-expenses", "-e",
    type=float,
    default=None,
    help="Monthly expenses for burn rate.",
)
@click.option(
    "--months", "-m",
    type=int,
    default=13,
    help="Months of history (default: 13).",
)
@click.option(
    "--json-output", "-j",
    is_flag=True,
    default=False,
    help="Output raw JSON.",
)
def main(
    stripe_key: str | None,
    bank_balance: float | None,
    monthly_expenses: float | None,
    months: int,
    json_output: bool,
) -> None:
    """SaaS metrics from your Stripe account. One command."""
    console = Console(theme=THEME)

    # Show banner (unless JSON mode)
    if not json_output:
        console.print()
        console.print(BANNER)
        console.print()

    # ── Interactive key prompt ───────────────────────────────────
    if not stripe_key:
        stripe_key = os.environ.get("STRIPE_SECRET_KEY")

    if not stripe_key:
        if json_output:
            print(json.dumps({"error": "STRIPE_SECRET_KEY not set"}))
            sys.exit(1)

        console.print("  [fikrah.dim]Connect your Stripe account to see your metrics.[/]")
        console.print()
        stripe_key = Prompt.ask(
            "  [fikrah.accent]Stripe API key[/]",
            password=True,
            console=console,
        )
        console.print()

    if not stripe_key or not stripe_key.strip():
        console.print("  [fikrah.error]No key provided. Exiting.[/]")
        sys.exit(1)

    stripe_key = stripe_key.strip()

    if not stripe_key.startswith("sk_"):
        console.print("  [fikrah.error]Invalid key format.[/] Must start with [bold]sk_live_[/] or [bold]sk_test_[/]")
        sys.exit(1)

    # ── Interactive bank balance prompt ──────────────────────────
    if bank_balance is None and not json_output:
        bal_input = Prompt.ask(
            "  [fikrah.accent]Bank balance[/] [fikrah.dim](for runway calc, or press Enter to skip)[/]",
            default="",
            console=console,
        )
        if bal_input.strip():
            try:
                bank_balance = float(bal_input.strip().replace(",", "").replace("$", "").replace("€", ""))
            except ValueError:
                console.print("  [fikrah.dim]Couldn't parse that — using Stripe balance instead.[/]")
        console.print()

    # ── Fetch ────────────────────────────────────────────────────
    if not json_output:
        console.print("  [fikrah.dim]Connecting to Stripe...[/]")
        console.print()

    with console.status("[fikrah.dim]  Fetching subscriptions, invoices, and customers...[/]", spinner="dots") if not json_output else _noop_context():
        try:
            from fikrah_metrics.stripe_client import fetch_stripe_data
            data = fetch_stripe_data(stripe_key, months=months)
        except Exception as e:
            if json_output:
                print(json.dumps({"error": str(e)}))
            else:
                console.print(f"  [fikrah.error]Stripe API error:[/] {e}")
            sys.exit(1)

    # ── Compute ──────────────────────────────────────────────────
    with console.status("[fikrah.dim]  Computing metrics...[/]", spinner="dots") if not json_output else _noop_context():
        from fikrah_metrics.metrics import compute_metrics
        metrics = compute_metrics(data, bank_balance=bank_balance, monthly_expenses=monthly_expenses)

    # ── Output ───────────────────────────────────────────────────
    if json_output:
        from dataclasses import asdict
        output = asdict(metrics)
        output["monthly_snapshots"] = [
            {"month": s["month"], "mrr": s["mrr"], "active_customers": s["active_customers"]}
            for s in output["monthly_snapshots"]
        ]
        print(json.dumps(output, indent=2, default=str))
    else:
        from fikrah_metrics.display import display_metrics
        display_metrics(metrics, console=console)


class _noop_context:
    """No-op context manager for JSON mode (no spinners)."""
    def __enter__(self): return self
    def __exit__(self, *a): pass


if __name__ == "__main__":
    main()
