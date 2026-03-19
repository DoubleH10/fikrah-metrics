"""Rich terminal output for SaaS metrics — Fikrah brand styling."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from fikrah_metrics.metrics import SaaSMetrics

THEME = Theme({
    "fikrah.brand": "bold #D1E95C",
    "fikrah.accent": "#D1E95C",
    "fikrah.dim": "#6b7c6e",
    "fikrah.green": "#22C55E",
    "fikrah.red": "#EF4444",
    "fikrah.amber": "#F59E0B",
    "fikrah.sage": "#E8F0ED",
})


def fmt_currency(value: float, currency: str = "usd") -> str:
    """Format currency value."""
    symbols = {"usd": "$", "eur": "€", "gbp": "£", "sar": "SAR "}
    symbol = symbols.get(currency.lower(), currency.upper() + " ")
    if abs(value) >= 1_000_000:
        return f"{symbol}{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{symbol}{value / 1_000:.1f}K"
    return f"{symbol}{value:,.0f}"


def fmt_pct(value: float, invert: bool = False) -> str:
    """Format percentage with color. invert=True means lower is better."""
    if value == 0:
        return "[fikrah.dim]0.0%[/]"
    positive_good = not invert
    if (value > 0 and positive_good) or (value < 0 and not positive_good):
        return f"[fikrah.green]+{value:.1f}%[/]" if value > 0 else f"[fikrah.green]{value:.1f}%[/]"
    return f"[fikrah.red]{value:+.1f}%[/]"


def health_badge(label: str, color: str) -> str:
    """Format a health badge."""
    return f"[{color}]● {label}[/]"


def display_metrics(metrics: SaaSMetrics, console: Console | None = None) -> None:
    """Render SaaS metrics to the terminal with Fikrah branding."""
    if console is None:
        console = Console(theme=THEME)

    c = metrics.currency

    # ── Hero: Revenue ────────────────────────────────────────────
    hero = Table(show_header=False, box=None, padding=(0, 4), expand=True)
    hero.add_column(justify="center")
    hero.add_column(justify="center")
    hero.add_column(justify="center")
    hero.add_column(justify="center")

    hero.add_row(
        f"[fikrah.dim]MRR[/]\n[bold #D1E95C]{fmt_currency(metrics.mrr, c)}[/]",
        f"[fikrah.dim]ARR[/]\n[bold]{fmt_currency(metrics.arr, c)}[/]",
        f"[fikrah.dim]NRR[/]\n[bold]{metrics.net_revenue_retention:.0f}%[/]",
        f"[fikrah.dim]Customers[/]\n[bold]{metrics.active_subscriptions}[/]",
    )

    console.print(Panel(
        hero,
        border_style="#D1E95C",
        title="[bold #D1E95C] ◆ Revenue [/]",
        title_align="left",
        padding=(1, 2),
    ))

    # ── MRR Breakdown ────────────────────────────────────────────
    breakdown = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    breakdown.add_column("", style="bold", min_width=18)
    breakdown.add_column("", justify="right", min_width=12)
    breakdown.add_column("", style="fikrah.dim")

    breakdown.add_row("MRR Growth", fmt_pct(metrics.mrr_growth_rate), "month-over-month")
    breakdown.add_row("New MRR", f"[fikrah.green]{fmt_currency(metrics.new_mrr, c)}[/]", "new customers")
    breakdown.add_row("Expansion", f"[fikrah.green]{fmt_currency(metrics.expansion_mrr, c)}[/]", "upgrades")
    breakdown.add_row("Contraction", f"[fikrah.amber]{fmt_currency(metrics.contraction_mrr, c)}[/]", "downgrades")
    breakdown.add_row("Churned", f"[fikrah.red]{fmt_currency(metrics.churned_mrr, c)}[/]", "cancelled")

    console.print(Panel(
        breakdown,
        border_style="#3a5a4a",
        title="[bold] MRR Waterfall [/]",
        title_align="left",
        padding=(1, 2),
    ))

    # ── Retention ────────────────────────────────────────────────
    retention = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    retention.add_column("", style="bold", min_width=26)
    retention.add_column("", justify="right", min_width=10)
    retention.add_column("", min_width=14)

    nrr_h = health_badge("Excellent", "fikrah.green") if metrics.net_revenue_retention >= 110 else \
             health_badge("Good", "fikrah.green") if metrics.net_revenue_retention >= 100 else \
             health_badge("Below 100%", "fikrah.red") if metrics.net_revenue_retention > 0 else "[fikrah.dim]—[/]"
    grr_h = health_badge("Strong", "fikrah.green") if metrics.gross_revenue_retention >= 90 else \
             health_badge("Needs work", "fikrah.amber") if metrics.gross_revenue_retention >= 80 else \
             health_badge("High churn", "fikrah.red") if metrics.gross_revenue_retention > 0 else "[fikrah.dim]—[/]"
    churn_h = health_badge("Low", "fikrah.green") if 0 < metrics.logo_churn_rate < 3 else \
               health_badge("Moderate", "fikrah.amber") if metrics.logo_churn_rate < 7 else \
               health_badge("High", "fikrah.red") if metrics.logo_churn_rate > 0 else "[fikrah.dim]—[/]"

    retention.add_row("Net Revenue Retention", f"{metrics.net_revenue_retention:.1f}%", nrr_h)
    retention.add_row("Gross Revenue Retention", f"{metrics.gross_revenue_retention:.1f}%", grr_h)
    retention.add_row("Logo Churn Rate", f"{metrics.logo_churn_rate:.1f}%", churn_h)
    retention.add_row("ARPU", fmt_currency(metrics.arpu, c), "[fikrah.dim]per customer[/]")

    console.print(Panel(
        retention,
        border_style="#3a5a4a",
        title="[bold] Retention [/]",
        title_align="left",
        padding=(1, 2),
    ))

    # ── Runway ───────────────────────────────────────────────────
    runway = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    runway.add_column("", style="bold", min_width=18)
    runway.add_column("", justify="right", min_width=14)

    runway.add_row("Cash Balance", f"[bold]{fmt_currency(metrics.cash_balance, c)}[/]")
    runway.add_row("Monthly Burn", fmt_currency(metrics.monthly_burn, c))

    if metrics.runway_months > 0:
        r_color = "fikrah.green" if metrics.runway_months > 12 else \
                  "fikrah.amber" if metrics.runway_months > 6 else "fikrah.red"
        runway.add_row("Runway", f"[{r_color}][bold]{metrics.runway_months:.0f} months[/][/]")
    else:
        runway.add_row("Runway", "[fikrah.green][bold]∞ Profitable[/][/]")

    console.print(Panel(
        runway,
        border_style="#3a5a4a",
        title="[bold] Runway [/]",
        title_align="left",
        padding=(1, 2),
    ))

    # ── MRR Trend ────────────────────────────────────────────────
    snapshots = metrics.monthly_snapshots
    if len(snapshots) >= 3:
        trend = Table(show_header=True, header_style="fikrah.dim", box=None, padding=(0, 1), expand=True)
        trend.add_column("Month", style="fikrah.dim", min_width=8)
        trend.add_column("MRR", justify="right", min_width=10)
        trend.add_column("Cust", justify="right", min_width=6)
        trend.add_column("", min_width=24)

        display_snaps = snapshots[-8:]  # last 8 months
        max_mrr = max((s.mrr for s in display_snaps), default=1) or 1

        for snap in display_snaps:
            bar_len = int(snap.mrr / max_mrr * 24) if snap.mrr > 0 else 0
            bar = "[#D1E95C]" + "█" * bar_len + "[/]" + "[#3a5a4a]" + "░" * (24 - bar_len) + "[/]"
            trend.add_row(
                snap.month,
                fmt_currency(snap.mrr, c),
                str(snap.active_customers),
                bar,
            )

        console.print(Panel(
            trend,
            border_style="#3a5a4a",
            title="[bold] MRR Trend [/]",
            title_align="left",
            padding=(1, 2),
        ))

    # ── Footer ───────────────────────────────────────────────────
    console.print()
    console.print("  [fikrah.dim]Track these metrics daily →[/] [bold #D1E95C]fikrah.io[/]")
    console.print("  [fikrah.dim]Questions? team@bloq-ai.net[/]")
    console.print()
