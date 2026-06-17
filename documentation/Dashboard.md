# Dashboard (Vite + React CSR)

Lightweight, client-rendered trading dashboard. Polls the REST API to display live portfolio positions, P&L, price charts, and trade history. Designed as an internal monitoring tool — quick to set up, no server process required beyond a static file host.

## Why it's separate from `dashboard-pro/`

- Different rendering model (CSR vs. SSR/RSC) — no server process to manage; the built output is a plain static SPA.
- The tradeoff: `VITE_API_KEY` is embedded in the client bundle at build time. Acceptable for an internal tool on a private network, but not suitable for public-facing deployment. See [`Dashboard_Pro.md`](Dashboard_Pro.md) for the server-rendered alternative that keeps the key out of the browser.
- Both apps live in one **pnpm workspace** (`pnpm-workspace.yaml` at the repo root), sharing a single `node_modules` store and installing together via `pnpm install`.

## Local development

```bash
# from the repo root
pnpm install

cp dashboard/.env.local.example dashboard/.env.local
# VITE_API_URL — base URL of the running API server (e.g. http://localhost:8000)
# VITE_API_KEY  — must match the API server's key

pnpm --filter dashboard dev
```

Visit `http://localhost:5173`.

## How auth works

All requests are made client-side from `src/api.ts`. The API key is read from `import.meta.env.VITE_API_KEY` and sent as an `X-API-Key` header on every fetch. Because Vite inlines `VITE_*` env vars at build time, the key is present in the compiled JS bundle.

To avoid exposing the key: keep this dashboard on a private network, or switch to [`dashboard-pro/`](../dashboard-pro/) which proxies all API calls through a Next.js server route.

## Components

| Component | What it shows |
|---|---|
| `Portfolio` | Open positions — entry price, current price, unrealised P&L |
| `PnlSummary` | Realised P&L by asset |
| `PriceChart` | 5-min OHLCV chart per asset (via `/api/v1/ohlcv/{asset}`) |
| `Trades` | Live trade history — side, price, USD value, reason |

All REST calls go through the typed helpers in `src/api.ts`. See [`API.md`](API.md) for the full endpoint reference.

## Build and deployment

```bash
pnpm --filter dashboard build   # output in dashboard/dist/
```

The `dist/` directory is a standard static SPA. Serve it with nginx using the config in `deploy/dashboard.nginx.conf`:

```bash
cp deploy/dashboard.nginx.conf /etc/nginx/sites-available/dashboard
# edit the root path to point at dashboard/dist/
nginx -t && systemctl reload nginx
```

No server process — only nginx is needed at runtime.

## Related

- [`dashboard-pro/`](../dashboard-pro/) — SSR + GraphQL version with server-side auth
- [`Dashboard_Pro.md`](Dashboard_Pro.md) — architecture and deployment guide for the pro dashboard
- [`API.md`](API.md) — REST and GraphQL endpoint reference
