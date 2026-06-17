# Dashboard Pro (Next.js SSR + GraphQL)

Server-rendered trading dashboard. Extends [`dashboard/`](../dashboard/) with SSR/RSC, GraphQL, per-route error/loading boundaries, and live polling — while keeping the API key out of the browser entirely.

See [`documentation/Dashboard_Pro.md`](../documentation/Dashboard_Pro.md) for a full architectural overview, including how auth differs from `dashboard/` and how the GraphQL proxy route works.

## Stack

- Next.js 15 (App Router, Server Components)
- Apollo Client (server-side SSR fetch + client-side polling via `/api/graphql` proxy)
- Tailwind CSS, Recharts
- TypeScript with generated GraphQL types (`codegen.ts`)

## Local development

```bash
# from the repo root — installs both dashboard/ and dashboard-pro/ deps at once
pnpm install

# copy and fill in the env file (server-only — never shipped to the browser)
cp dashboard-pro/.env.local.example dashboard-pro/.env.local
# API_KEY must match the running API server's key

pnpm --filter dashboard-pro dev
```

Visit `http://localhost:3000` (redirects to `/portfolio`).

## Production deployment

```bash
cd dashboard-pro
pnpm build
pnpm start   # listens on PORT env var, default 3001
```

Or install the systemd unit:

```bash
cp deploy/dashboard-pro.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now dashboard-pro
```

The unit reuses the same encrypted credential file as the API service (`/etc/credstore/api_key.cred`) — no second secret to manage. See [`documentation/DASHBOARD_PRO.md`](../documentation/DASHBOARD_PRO.md#production-deployment) for details.

## GraphQL type generation

```bash
pnpm --filter dashboard-pro codegen
```

Regenerate `lib/graphql/` types after changing `schema.graphql` or any `.graphql` query file.

## Related

- [`dashboard/`](../dashboard/) — simpler CSR version (Vite + REST)
- [`documentation/Dashboard_Pro.md`](../documentation/Dashboard_Pro.md) — architecture, auth design, deployment guide
- [`documentation/API.md`](../documentation/API.md) — REST and GraphQL endpoint reference
