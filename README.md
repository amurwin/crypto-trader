# Crypto Trader — API & Dashboards

A FastAPI + GraphQL backend and two frontends (a lightweight client-rendered
dashboard and an enterprise-style server-rendered one) for monitoring a
live crypto trading system: portfolio state, trade history, P&L, and price
charts.

This repo is intentionally **read-only and strategy-agnostic** — it serves
data, it doesn't decide what to trade. The actual trading strategy
(indicators, entry/exit logic, tuned parameters, the live trading bot)
lives in a private repo and is not part of this codebase. Nothing here
hardcodes which assets are traded; the asset list is read from a database
table at runtime.

## Architecture

```
api/            FastAPI app: REST (/api/v1/*) + GraphQL (/graphql), shared
                data-access layer over PostgreSQL. Static API-key auth.
dashboard/      Vite + React, client-side rendered, consumes the REST API.
dashboard-pro/  Next.js (App Router), server-rendered via Apollo Client RSC
                support, GraphQL only. API key never reaches the browser.
exchanges/      Generic exchange API adapters (Binance.US, Kraken) — order
                placement / market data mechanics only, no trading logic.
```

Both dashboards and the API are fully decoupled from any private code at
runtime: the API queries a small `assets` table for the tradeable-asset
list (symbol, candle-table name, exchange) instead of importing it from
anywhere, so this repo never needs the private strategy repo present to
run.

See [documentation/API.md](documentation/API.md), [documentation/DASHBOARD_PRO.md](documentation/DASHBOARD_PRO.md),
and [documentation/Database.md](documentation/Database.md) for details on
each piece.

## Running locally

**1. API server**
```bash
cp api/.env.example api/.env   # fill in DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD/API_KEY
pipenv install
set -a && source api/.env && set +a
pipenv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
The database needs an `assets` table populated with at least one row (see
`documentation/Database.md`) — that data is supplied by whatever private
process owns the trading strategy; this repo only reads it.

**2. Dashboards** (from repo root — both share a pnpm workspace)
```bash
pnpm install
cp dashboard/.env.example dashboard/.env               # VITE_API_KEY must match api/.env's API_KEY
cp dashboard-pro/.env.local.example dashboard-pro/.env.local   # same key
pnpm --filter dashboard dev        # Vite dashboard
pnpm --filter dashboard-pro dev    # Next.js dashboard
```

## Deployment

`deploy/api.service` and `deploy/dashboard-pro.service` are systemd units
for production deployment — see the comments in each file and
`documentation/API.md` for the full setup (encrypted credentials via
`systemd-creds`, etc).
