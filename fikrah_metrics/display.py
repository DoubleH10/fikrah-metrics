"""Rich terminal output for SaaS metrics."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from fikrah_metrics.metrics import SaaSMetrics

THEME = Theme({
    "fikrah.lime": "#D1E95C",
    "fikrah.green": "#22C55E",
    "fikrah.red": "#EF4444",
    "fikrah.dim": "#6B7280",
    "fikrah.sage": "#E8F0ED",
})

BANNER = """[#D1E95C]
  ╔═╗╦╦╔═╦═╗╔═╗╦ ╦
  ╠╣ ║╠╩╗╠╦╝╠═╣╠═╣  [dim]metrics[/dim]
  ╚  ╩╩ ╩╩╚═╩ ╩╩ ╩
[/#D1E95C]"""


def fmt_currency(value: float, currency: str = "usd") -> str:
    """Format currency value."""
    symbols = {"usd": "$", "eur": "€", "gbp": "£", "sar": "SAR "}
    symbol = symbols.get(currency.lower(), currency.upper() + " ")
    if value >= 1_000_000:
        return f"{symbol}{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{symbol}{value / 1_000:.1f}K"
    return f"{symbol}{value:,.0f}"


def fmt_pct(value: float) -> str:
    """Format percentage with color."""
    if value > 0:
        return f"[#22C55E]+{value:.1f}%[/#22C55E]"
    if value < 0:
        return f"[#EF4444]{value:.1f}%[/#EF4444]"
    return f"[dim]{value:.1f}%[/dim]"


def display_metrics(metrics: SaaSMetrics, console: Console | None = None) -> None:
    """Render SaaS metrics to the terminal."""
    if console is None:
        console = Console(theme=THEME)

    console.print(BANNER)

    # ── Hero Metrics ─────────────────────────────────────────────
    hero = Table(show_header=False, box=None, padding=(0, 3))
    hero.add_column(justify="center")
    hero.add_column(justify="center")
    hero.add_column(justify="center")
    hero.add_column(justify="center")

    hero.add_row(
        f"[dim]MRR[/dim]\n[bold #D1E95C]{fmt_currency(metrics.mrr, metrics.currency)}[/]",
        f"[dim]ARR[/dim]\n[bold]{fmt_currency(metrics.arr, metrics.currency)}[/]",
        f"[dim]NRR[/dim]\n[bold]{metrics.net_revenue_retention:.0f}%[/]",
        f"[dim]Customers[/dim]\n[bold]{metrics.active_subscriptions}[/]",
    )

    console.print(Panel(hero, border_style="#D1E95C", title="[bold]Revenue[/]", title_align="left"))

    # ── MRR Breakdown ────────────────────────────────────────────
    breakdown = Table(show_header=True, header_style="dim", box=None, padding=(0, 2))
    breakdown.add_column("Metric", style="bold")
    breakdown.add_column("Value", justify="right")
    breakdown.add_column("", justify="left")

    breakdown.add_row("MRR Growth", fmt_pct(metrics.mrr_growth_rate), "month-over-month")
    breakdown.add_row("New MRR", fmt_currency(metrics.new_mrr, metrics.currency), "from new customers")
    breakdown.add_row("Expansion", fmt_currency(metrics.expansion_mrr, metrics.currency), "upgrades & add-ons")
    breakdown.add_row("Contraction", fmt_currency(metrics.contraction_mrr, metrics.currency), "downgrades")
    breakdown.add_row("Churned", fmt_currency(metrics.churned_mrr, metrics.currency), "cancelled")

    console.print(Panel(breakdown, border_style="dim", title="[bold]MRR Breakdown[/]", title_align="left"))

    # ── Retention ────────────────────────────────────────────────
    retention = Table(show_header=True, header_style="dim", box=None, padding=(0, 2))
    retention.add_column("Metric", style="bold")
    retention.add_column("Value", justify="right")
    retention.add_column("Health", justify="left")

    nrr_health = "[#22C55E]Excellent[/]" if metrics.net_revenue_retention >= 110 else \
                 "[#22C55E]Good[/]" if metrics.net_revenue_retention >= 100 else \
                 "[#EF4444]Below 100%[/]" if metrics.net_revenue_retention > 0 else "[dim]N/A[/dim]"
    grr_health = "[#22C55E]Strong[/]" if metrics.gross_revenue_retention >= 90 else \
                 "[yellow]Needs work[/]" if metrics.gross_revenue_retention >= 80 else \
                 "[#EF4444]High churn[/]" if metrics.gross_revenue_retention > 0 else "[dim]N/A[/dim]"
    churn_health = "[#22C55E]Low[/]" if metrics.logo_churn_rate < 3 else \
                   "[yellow]Moderate[/]" if metrics.logo_churn_rate < 7 else \
                   "[#EF4444]High[/]" if metrics.logo_churn_rate > 0 else "[dim]N/A[/dim]"

    retention.add_row("Net Revenue Retention", f"{metrics.net_revenue_retention:.1f}%", nrr_health)
    retention.add_row("Gross Revenue Retention", f"{metrics.gross_revenue_retention:.1f}%", grr_health)
    retention.add_row("Logo Churn Rate", f"{metrics.logo_churn_rate:.1f}%", churn_health)
    retention.add_row("ARPU", fmt_currency(metrics.arpu, metrics.currency), "avg revenue per user")

    console.print(Panel(retention, border_style="dim", title="[bold]Retention[/]", title_align="left"))

    # ── Runway ───────────────────────────────────────────────────
    runway = Table(show_header=False, box=None, padding=(0, 2))
    runway.add_column("Metric", style="bold")
    runway.add_column("Value", justify="right")

    runway.add_row("Cash Balance", fmt_currency(metrics.cash_balance, metrics.currency))
    runway.add_row("Monthly Burn", fmt_currency(metrics.monthly_burn, metrics.currency))

    if metrics.runway_months > 0:
        runway_color = "#22C55E" if metrics.runway_months > 12 else \
                       "yellow" if metrics.runway_months > 6 else "#EF4444"
        runway.add_row("Runway", f"[{runway_color}]{metrics.runway_months:.0f} months[/]")
    else:
        runway.add_row("Runway", "[dim]Infinite (profitable)[/dim]")

    console.print(Panel(runway, border_style="dim", title="[bold]Runway[/]", title_align="left"))

    # ── MRR Trend (sparkline) ────────────────────────────────────
    if len(metrics.monthly_snapshots) >= 3:
        trend = Table(show_header=True, header_style="dim", box=None, padding=(0, 1))
        trend.add_column("Month", style="dim")
        trend.add_column("MRR", justify="right")
        trend.add_column("Customers", justify="right")
        trend.add_column("", justify="left")

        for snap in metrics.monthly_snapshots[-6:]:  # last 6 months
            bar_len = int(snap.mrr / max(s.mrr for s in metrics.monthly_snapshots[-6:]) * 20) if snap.mrr > 0 else 0
            bar = "[#D1E95C]" + "█" * bar_len + "[/]"
            trend.add_row(
                snap.month,
                fmt_currency(snap.mrr, metrics.currency),
                str(snap.active_customers),
                bar,
            )

        console.print(Panel(trend, border_style="dim", title="[bold]MRR Trend[/]", title_align="left"))

    # ── Footer ───────────────────────────────────────────────────
    console.print()
    console.print("[dim]  Track these metrics daily →[/dim] [bold #D1E95C]fikrah.io[/]")
    console.print()
