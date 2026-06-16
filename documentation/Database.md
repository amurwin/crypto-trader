# Database Reference

PostgreSQL, host/port/db/user configured via env vars (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — see `api/.env.example`). No host or credentials are documented here; see your private deployment notes.

---

## `assets` Table

The single source of truth for which assets are tradeable and where their data lives. No other file or table name is hardcoded anywhere in this repo — everything else (the API, the dashboards, the data-ingestion script) looks up asset/table/exchange info from this table at runtime.

| Column | Type | Description |
|---|---|---|
| `symbol` | TEXT (PK) | Ticker, e.g. `LTC` |
| `ohlcv_table` | TEXT | Name of the per-asset candle table holding this asset's OHLCV bars |
| `exchange` | TEXT | Which exchange adapter (`exchanges/`) this asset trades on |
| `enabled` | BOOLEAN | Whether this asset is currently active |

```sql
CREATE TABLE assets (
  symbol      TEXT PRIMARY KEY,
  ohlcv_table TEXT NOT NULL,
  exchange    TEXT NOT NULL,
  enabled     BOOLEAN NOT NULL DEFAULT true
);
CREATE INDEX idx_assets_exchange ON assets (exchange);
```

Row data (the actual ticker list) is seeded privately and is never committed to this repo.

---

## Price Data Tables

One table per asset (name given by `assets.ohlcv_table`), all following the same schema:

| Column | Type | Description |
|---|---|---|
| `ts` | TIMESTAMPTZ (PK) | Bar open time (5-min aligned, UTC) |
| `open` | NUMERIC | Open price |
| `high` | NUMERIC | High price |
| `low` | NUMERIC | Low price |
| `close` | NUMERIC | Close price |
| `vol` | NUMERIC | Volume (base asset) |

---

## Trader State Tables

### `trader_cooldowns`

Internal state used by the private live-trading engine — not read by the public API or dashboards. See the private repo's documentation for schema and behavior.

### `live_trades`

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL (PK) | Auto-increment |
| `ts` | TIMESTAMPTZ | Time the order was placed |
| `asset` | TEXT | Asset name |
| `side` | TEXT | `BUY` or `SELL` |
| `price` | DOUBLE PRECISION | Fill price |
| `coins` | DOUBLE PRECISION | Quantity traded |
| `usd` | DOUBLE PRECISION | USD value (spent on buy, received on sell) |
| `pnl_pct` | DOUBLE PRECISION | P&L % (SELL only) |
| `reason` | TEXT | Exit reason: `TARGET`, `STOP`, `TARGET (realtime)`, `STOP (realtime)`, `TARGET (gap open)`, `STOP (gap open)`, `GAP/HORIZON`, `DEAD MARKET` (SELL only) |

---

## Useful Queries

**Check data coverage per asset** (run per `ohlcv_table` value from `assets`, substituted via your own tooling — table names can't be parameterized directly in SQL):
```sql
SELECT MIN(ts) AS first_bar, MAX(ts) AS last_bar, COUNT(*) AS total_bars
FROM <ohlcv_table>;
```

**Find gaps > 30 min in a table:**
```sql
SELECT ts, next_ts, ROUND(EXTRACT(EPOCH FROM (next_ts - ts))/60) AS gap_min
FROM (
    SELECT ts, LEAD(ts) OVER (ORDER BY ts) AS next_ts FROM <ohlcv_table>
) t
WHERE EXTRACT(EPOCH FROM (next_ts - ts)) > 1800
ORDER BY ts;
```

**Recent live trades:**
```sql
SELECT ts, asset, side, price, usd, pnl_pct, reason
FROM live_trades
ORDER BY ts DESC
LIMIT 20;
```

**P&L summary by asset:**
```sql
SELECT asset,
       COUNT(*) FILTER (WHERE side = 'SELL') AS trades,
       ROUND(AVG(pnl_pct)::numeric, 2) AS avg_pnl_pct,
       ROUND(SUM(pnl_pct)::numeric, 2) AS total_pnl_pct,
       COUNT(*) FILTER (WHERE side = 'SELL' AND pnl_pct > 0) AS wins,
       COUNT(*) FILTER (WHERE side = 'SELL' AND pnl_pct <= 0) AS losses
FROM live_trades
GROUP BY asset
ORDER BY total_pnl_pct DESC;
```

**30-day trade volume:**
```sql
SELECT ROUND(SUM(usd)::numeric, 2) AS total_usd_volume
FROM live_trades
WHERE ts >= NOW() - INTERVAL '30 days';
```

**Current cooldowns:**
```sql
SELECT * FROM trader_cooldowns ORDER BY bars DESC;
```
