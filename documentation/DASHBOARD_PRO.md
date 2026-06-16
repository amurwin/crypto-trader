# Dashboard Pro (Next.js SSR + GraphQL)

Enterprise-grade companion to `dashboard/` — server-rendered, GraphQL-backed, with
per-route error/loading boundaries and live polling. The simple `dashboard/`
(Vite + React, REST, client-rendered) is unaffected and continues to work as before.

## Why it's separate from `dashboard/`

- Different rendering model (SSR/RSC vs. CSR) makes a shared component library more
  trouble than it's worth at this size.
- Both apps live in one **pnpm workspace** (`pnpm-workspace.yaml` at the repo root) so
  they share a single `node_modules` content-addressable store instead of duplicating
  React/TypeScript/Tailwind/Recharts on disk, and both install via a single
  `pnpm install` from the repo root.

## Local development

```bash
# from the repo root — installs both dashboard/ and dashboard-pro/ deps at once
pnpm install

# copy and fill in the env file (server-only — never shipped to the browser)
cp dashboard-pro/.env.local.example dashboard-pro/.env.local
# edit dashboard-pro/.env.local: API_KEY must match the running API server's key

pnpm --filter dashboard-pro dev
```

Visit `http://localhost:3000` (redirects to `/portfolio`).

## How auth works here (different from `dashboard/`)

`dashboard/`'s Vite app ships its API key in the client bundle (`VITE_API_KEY`) — fine
for an internal test tool, but not how you'd want it in an "enterprise" build.

`dashboard-pro` never sends the key to the browser:
- Server Components (initial SSR fetch per route) call the GraphQL API directly from
  the Next.js server process, attaching `X-API-Key` via `lib/apollo-client.ts`.
- Client Components (live polling, filter re-queries) call a same-origin route handler
  at `/api/graphql` (`app/api/graphql/route.ts`), which proxies to the real GraphQL
  endpoint and attaches the key server-side. The browser only ever talks to
  `/api/graphql` with no key attached.
- `lib/api-key.ts` mirrors `api/auth.py`'s credential-loading order: a systemd
  credential file (`$CREDENTIALS_DIRECTORY/api_key`) first, then the `API_KEY` env var.

## Production deployment

```bash
cd dashboard-pro
pnpm build
pnpm start   # or use the systemd unit below
```

`deploy/dashboard-pro.service` mirrors `deploy/api.service`'s pattern and **reuses the
same encrypted credential file** (`/etc/credstore/api_key.cred`) — no second secret to
manage. Install it the same way as the API service:

```bash
cp deploy/dashboard-pro.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable dashboard-pro
systemctl start dashboard-pro
```

Runs on port 3001 by default (set via the `PORT` env var in the unit) so it can sit
alongside `api.service` (port 8000) and the existing Vite dashboard if you choose to
serve that too.

## Verifying the API key never reaches the browser

```bash
pnpm --filter dashboard-pro build
grep -r "your-actual-api-key" dashboard-pro/.next/static || echo "key not found in client bundle (expected)"
```
