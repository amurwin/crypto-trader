# Deployment Guide

## Requirements

- Python 3+, pipenv (`pip install pipenv`)
- Node.js 22+, pnpm (`npm install -g pnpm`)
- nginx
- PostgreSQL (running separately — see `documentation/Database.md` for schema)
- A sibling clone of the private repo at `../crypto-trader-private/` (for the live trading bot)

## Repository Layout on Server

```
/root/projects/
  crypto-trader/           # this repo — API + dashboards
  crypto-trader-private/   # private repo — live trader + strategy
```

---

## First-Time Setup

### 1. Clone repos

```bash
git clone git@github.com:amurwin/crypto-trader.git /root/projects/crypto-trader
git clone git@github.com:amurwin/crypto-trader-private.git /root/projects/crypto-trader-private
```

### 2. Python dependencies (API)

```bash
cd /root/projects/crypto-trader
pipenv install
```

### 3. Node dependencies and dashboard builds

```bash
cd /root/projects/crypto-trader
pnpm install
```

Create env files **before** building — Vite bakes `VITE_*` vars into the bundle at build time:

```bash
cp dashboard/.env.example dashboard/.env
# Edit dashboard/.env — set VITE_API_URL to the network-accessible IP of this server
# (not localhost — this URL is resolved by the browser, not the server)
cp dashboard-pro/.env.local.example dashboard-pro/.env.local
# Edit dashboard-pro/.env.local — set API_KEY and GRAPHQL_URL
```

Then build:

```bash
pnpm --filter dashboard build         # outputs to dashboard/dist/
pnpm --filter dashboard-pro build     # outputs to dashboard-pro/.next/
```

### 4. API env file

```bash
cp api/.env.example api/.env
# Edit api/.env — set API_KEY, DB_HOST, DB_PASSWORD
```

### 5. Install systemd services

```bash
cp deploy/api.service /etc/systemd/system/
cp deploy/dashboard-pro.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable api.service dashboard-pro.service
systemctl start api.service dashboard-pro.service
```

### 6. Install nginx (CSR dashboard)

```bash
apt-get install -y nginx
# nginx.conf: change 'user www-data' to 'user root' if serving from /root/
cp deploy/dashboard.nginx.conf /etc/nginx/sites-available/dashboard
ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/dashboard
nginx -t && systemctl restart nginx
```

---

## Service Management

```bash
systemctl status api.service
systemctl status dashboard-pro.service
systemctl restart api.service
journalctl -u api.service -f
journalctl -u dashboard-pro.service -f
```

---

## Ports

| Service | Port |
|---|---|
| API | 8000 |
| Dashboard Pro (Next.js SSR) | 3001 |
| Dashboard (CSR, nginx) | 3000 |

---

## Updating

```bash
cd /root/projects/crypto-trader
git pull
pnpm --filter dashboard build
pnpm --filter dashboard-pro build
systemctl restart api.service dashboard-pro.service
# nginx serves static files directly — no restart needed after dashboard rebuild
```

---

## Troubleshooting

**`pipenv: command not found`**
```bash
pip install pipenv --break-system-packages
```

**`Python 3.12 was not found` during `pipenv install`**
The Pipfile requires `python_version = "3"` (not a specific minor version). If you see this error, the Pipfile has an old pin — update it and re-run.

**`api.service` exits with `status=203/EXEC`**
systemd does not expand globs in `ExecStart`. The service must use `pipenv run uvicorn ...` with `PIPENV_PIPFILE` set, not a glob path like `virtualenvs/crypto-trader-*/bin/uvicorn`.

**`dashboard-pro.service` exits with `ERR_VM_DYNAMIC_IMPORT_CALLBACK_MISSING`**
`/usr/bin/pnpm` is the broken corepack shim. Use `/usr/local/bin/pnpm` (the npm-installed binary). Install with `npm install -g pnpm`.

**nginx 500: `Permission denied` on `/root/projects/...`**
nginx runs as `www-data` by default. Change `user www-data;` to `user root;` in `/etc/nginx/nginx.conf` when serving from `/root/`.

**CSR dashboard loads but API calls fail (`Load failed`)**
`VITE_API_URL` must be the network-accessible address of the server (e.g. `http://192.168.4.201:8000`), not `http://localhost:8000`. The URL is resolved by the browser, not the server. Rebuild after updating `.env`.

**CSR dashboard shows `The string did not match the expected pattern`**
The dashboard was built before `dashboard/.env` was created, so `VITE_API_KEY` is empty in the bundle. Create the env file first, then rebuild.
