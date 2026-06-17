# Dashboard (Vite + React)

Client-rendered trading dashboard. Displays live portfolio positions, P&L summary, price charts, and trade history by polling the REST API.

## Stack

- React 19, TypeScript, Tailwind CSS
- Recharts for price/P&L visualisation
- Vite for dev server and build

## Local development

```bash
# from the repo root
pnpm install

# copy and fill in the env file
cp dashboard/.env.local.example dashboard/.env.local
# VITE_API_URL — base URL of the running API server (e.g. http://localhost:8000)
# VITE_API_KEY  — must match the API server's key

pnpm --filter dashboard dev
```

Visit `http://localhost:5173`.

> **Note on the API key**: `VITE_API_KEY` is embedded in the client bundle at build time. This is acceptable for an internal tool but not for a public-facing deployment — see [`dashboard-pro/`](../dashboard-pro/) for a server-rendered build that keeps the key out of the browser. See [`documentation/Dashboard.md`](../documentation/Dashboard.md) for a full architectural overview.

## Build

```bash
pnpm --filter dashboard build   # output in dashboard/dist/
```

The built `dist/` is a standard static SPA. Serve it behind nginx (see [`deploy/`](../deploy/)) or any static host.

## Components

| Component | What it shows |
|---|---|
| `Portfolio` | Open positions with entry price, current price, and unrealised P&L |
| `PnlSummary` | Realised P&L by asset over a selectable window |
| `PriceChart` | 5-min OHLCV candlestick / line chart per asset |
| `Trades` | Live trade history with side, price, USD value, and reason |

All data fetching lives in [`src/api.ts`](src/api.ts) and calls the REST endpoints documented in [`documentation/API.md`](../documentation/API.md).

## Related

- [`dashboard-pro/`](../dashboard-pro/) — SSR/GraphQL version with the API key kept server-side
- [`documentation/API.md`](../documentation/API.md) — full REST and GraphQL reference
