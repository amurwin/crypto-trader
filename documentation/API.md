# API Server

FastAPI + Strawberry GraphQL server exposing historical OHLCV data, live trades, P&L, and portfolio.

## Endpoints

All endpoints require `X-API-Key: <key>` header.

### REST  (`/api/v1/`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/assets` | Tradeable assets. Params: `exchange` (optional) |
| GET | `/api/v1/ohlcv/{asset}` | 5-min OHLCV bars. Params: `limit`, `start`, `end` |
| GET | `/api/v1/trades` | Live trade history. Params: `asset`, `side`, `limit`, `since` |
| GET | `/api/v1/pnl` | P&L summary by asset. Params: `since` |
| GET | `/api/v1/portfolio` | Open positions with live prices + cash estimate |
| GET | `/health` | Health check (no auth required) |

The asset list is sourced entirely from the database (`assets` table) — no asset/ticker names are hardcoded anywhere in this codebase.

### GraphQL  (`/graphql`)

Same data as REST. POST to `/graphql` with `X-API-Key` header.

```graphql
{
  assets {
    symbol exchange
  }
  portfolio {
    cash invested total
    positions {
      asset coins entryPrice currentPrice marketValue unrealizedPnlPct
    }
  }
  trades(limit: 20) {
    ts asset side price usd pnlPct reason
  }
  pnl {
    asset trades wins losses avgPnlPct totalPnlPct
  }
  ohlcv(asset: "BTC", limit: 100) {
    ts open high low close vol
  }
}
```

## Deployment

### 1. Install dependencies on server
```bash
cd /root/projects/crypto-trader
pipenv install
```

### 2. Set up systemd credentials (machine-bound, encrypted)
```bash
# Generate a random API key
API_KEY=$(openssl rand -hex 32)
echo "Your API key: $API_KEY"

# Encrypt and store credentials
mkdir -p /etc/credstore
echo -n "$API_KEY"       | systemd-creds encrypt --name=api_key    - /etc/credstore/api_key.cred
echo -n 'your-db-pass'   | systemd-creds encrypt --name=db_password - /etc/credstore/db_password.cred
chmod 600 /etc/credstore/*.cred
```

### 3. Install and start the service
```bash
cp /root/projects/crypto-trader/deploy/api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable api
systemctl start api
systemctl status api
```

### 4. Verify
```bash
curl -H 'X-API-Key: YOUR_KEY' http://localhost:8000/api/v1/portfolio
```

## Security notes

- Credentials are encrypted with the machine's TPM/unique key via `systemd-creds`
- The encrypted `.cred` files can be committed to the **private** config repo — they are useless without the originating machine
- The API key is never stored in plaintext on disk
- GraphiQL playground is disabled in production (`graphql_ide=None`)
- No Swagger/Redoc UI exposed (`docs_url=None`)
