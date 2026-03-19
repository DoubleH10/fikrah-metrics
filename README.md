# fikrah-metrics

SaaS metrics from your Stripe account. One command.

```bash
pip install fikrah-metrics
fikrah-metrics --stripe-key sk_live_xxx
```

```
  ╔═╗╦╦╔═╦═╗╔═╗╦ ╦
  ╠╣ ║╠╩╗╠╦╝╠═╣╠═╣  metrics
  ╚  ╩╩ ╩╩╚═╩ ╩╩ ╩

┌─ Revenue ────────────────────────────────────┐
│  MRR          ARR          NRR    Customers  │
│  $8.2K        $98.4K       112%   47         │
└──────────────────────────────────────────────┘
┌─ MRR Breakdown ──────────────────────────────┐
│  MRR Growth    +12.3%     month-over-month   │
│  New MRR       $1.2K      from new customers │
│  Expansion     $400       upgrades & add-ons │
│  Contraction   $0         downgrades         │
│  Churned       $200       cancelled          │
└──────────────────────────────────────────────┘
┌─ Retention ──────────────────────────────────┐
│  Net Revenue Retention    112.0%   Excellent │
│  Gross Revenue Retention   97.5%   Strong    │
│  Logo Churn Rate            2.1%   Low       │
│  ARPU                      $174    per user  │
└──────────────────────────────────────────────┘
┌─ Runway ─────────────────────────────────────┐
│  Cash Balance     $84,000                    │
│  Monthly Burn     $6,560                     │
│  Runway           13 months                  │
└──────────────────────────────────────────────┘

  Track these metrics daily → fikrah.io
```

## What you get

| Metric | Description |
|--------|-------------|
| **MRR** | Monthly Recurring Revenue from active subscriptions |
| **ARR** | Annual run rate (MRR × 12) |
| **NRR** | Net Revenue Retention — are existing customers growing? |
| **GRR** | Gross Revenue Retention — how much revenue are you keeping? |
| **Logo Churn** | Customer churn rate |
| **ARPU** | Average Revenue Per User |
| **MRR Growth** | Month-over-month growth rate |
| **New / Expansion / Contraction / Churned MRR** | Full MRR waterfall |
| **Runway** | Months of cash remaining at current burn |
| **MRR Trend** | Visual chart of last 6 months |

## Usage

### Basic
```bash
fikrah-metrics --stripe-key sk_live_xxx
```

### With bank balance for accurate runway
```bash
fikrah-metrics -k sk_live_xxx --bank-balance 84000
```

### With explicit monthly expenses
```bash
fikrah-metrics -k sk_live_xxx --bank-balance 84000 --monthly-expenses 12000
```

### JSON output (pipe to jq, save to file, send to API)
```bash
fikrah-metrics -k sk_live_xxx --json-output > metrics.json
fikrah-metrics -k sk_live_xxx -j | jq '.mrr, .arr, .net_revenue_retention'
```

### Environment variable
```bash
export STRIPE_SECRET_KEY=sk_live_xxx
fikrah-metrics
```

### Test mode
```bash
fikrah-metrics -k sk_test_xxx --test
```

## Install

```bash
pip install fikrah-metrics
```

Or with [uv](https://github.com/astral-sh/uv):
```bash
uvx fikrah-metrics --stripe-key sk_live_xxx
```

## Requirements

- Python 3.10+
- A Stripe account with subscriptions

## How it works

1. Fetches subscriptions, invoices, and customers from the Stripe API
2. Computes MRR from active subscription line items (handles monthly, annual, weekly billing)
3. Builds monthly revenue snapshots from paid invoices
4. Calculates retention metrics (NRR, GRR, churn) from month-over-month changes
5. Estimates runway from cash balance and burn rate

All computation happens locally. Your Stripe key is only used to read data — no writes, no webhooks, no stored credentials.

## FAQ

**Is this accurate?**
MRR is computed directly from active Stripe subscriptions (the source of truth). Retention metrics are derived from paid invoices, which is the most reliable signal. For very complex billing (usage-based, metered), some approximation is involved.

**Can I use this with Stripe test mode?**
Yes. Pass `--test` with a `sk_test_*` key.

**What about non-Stripe revenue?**
Use `--bank-balance` to include your actual bank balance. Non-subscription revenue (one-time charges, services) isn't included in MRR — that's by design.

**Is my Stripe key safe?**
Your key is used in-memory for one API session. It's never stored, logged, or transmitted anywhere except to Stripe's API.

## License

MIT

---

*Powered by [Fikrah](https://fikrah.io) — the financial control layer for AI agents.*
