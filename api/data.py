"""
Data access layer — queries PostgreSQL and Binance public API.
Used by both REST routes and GraphQL resolvers.
"""

from __future__ import annotations
import datetime
import requests as _requests

import psycopg_pool

from api.models import OhlcvBar, Trade, Position, Portfolio, AssetPnl, Asset

FEE_BUY  = 0.0002
FEE_SELL = 0.0002
_BINANCE_TICKER = 'https://api.binance.us/api/v3/ticker/price'


async def fetch_assets(
    pool: psycopg_pool.AsyncConnectionPool,
    exchange: str | None = None,
) -> list[Asset]:
    where = 'WHERE enabled AND exchange = %s' if exchange else 'WHERE enabled'
    params = [exchange] if exchange else []
    async with pool.connection() as conn:
        rows = await (await conn.execute(
            f"SELECT symbol, exchange FROM assets {where} ORDER BY symbol",
            params,
        )).fetchall()
    return [Asset(symbol=r['symbol'], exchange=r['exchange']) for r in rows]


async def _asset_table(pool: psycopg_pool.AsyncConnectionPool, asset: str) -> str | None:
    async with pool.connection() as conn:
        row = await (await conn.execute(
            "SELECT ohlcv_table FROM assets WHERE symbol = %s AND enabled", (asset.upper(),),
        )).fetchone()
    return row['ohlcv_table'] if row else None


async def asset_exists(pool: psycopg_pool.AsyncConnectionPool, asset: str) -> bool:
    return await _asset_table(pool, asset) is not None


async def fetch_ohlcv(
    pool: psycopg_pool.AsyncConnectionPool,
    asset: str,
    limit: int = 200,
    start: datetime.datetime | None = None,
    end:   datetime.datetime | None = None,
) -> list[OhlcvBar]:
    table = await _asset_table(pool, asset)
    if table is None:
        return []
    where_clauses = []
    params: list = []
    if start:
        where_clauses.append(f'ts >= %s')
        params.append(start)
    if end:
        where_clauses.append(f'ts <= %s')
        params.append(end)
    where = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
    params.append(limit)
    async with pool.connection() as conn:
        rows = await (await conn.execute(
            f"SELECT ts, open, high, low, close, vol FROM {table} {where} "
            f"ORDER BY ts DESC LIMIT %s",
            params,
        )).fetchall()
    return [OhlcvBar(
        ts=r['ts'], open=float(r['open']), high=float(r['high']),
        low=float(r['low']), close=float(r['close']), vol=float(r['vol']),
    ) for r in reversed(rows)]


async def fetch_trades(
    pool: psycopg_pool.AsyncConnectionPool,
    asset:  str | None = None,
    side:   str | None = None,
    limit:  int = 100,
    since:  datetime.datetime | None = None,
) -> list[Trade]:
    where_clauses = []
    params: list = []
    if asset:
        where_clauses.append('asset = %s')
        params.append(asset.upper())
    if side:
        where_clauses.append('side = %s')
        params.append(side.upper())
    if since:
        where_clauses.append('ts >= %s')
        params.append(since)
    where = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
    params.append(limit)
    async with pool.connection() as conn:
        rows = await (await conn.execute(
            f"SELECT id, ts, asset, side, price, coins, usd, pnl_pct, reason "
            f"FROM live_trades {where} ORDER BY ts DESC LIMIT %s",
            params,
        )).fetchall()
    return [Trade(**r) for r in rows]


async def fetch_pnl_summary(
    pool: psycopg_pool.AsyncConnectionPool,
    since: datetime.datetime | None = None,
) -> list[AssetPnl]:
    where = 'WHERE side = %s' + (' AND ts >= %s' if since else '')
    params: list = ['SELL']
    if since:
        params.append(since)
    async with pool.connection() as conn:
        rows = await (await conn.execute(
            f"SELECT asset, "
            f"  COUNT(*) AS trades, "
            f"  COUNT(*) FILTER (WHERE pnl_pct > 0) AS wins, "
            f"  COUNT(*) FILTER (WHERE pnl_pct <= 0) AS losses, "
            f"  COALESCE(ROUND(AVG(pnl_pct)::numeric, 4), 0) AS avg_pnl_pct, "
            f"  COALESCE(ROUND(SUM(pnl_pct)::numeric, 4), 0) AS total_pnl_pct "
            f"FROM live_trades {where} "
            f"GROUP BY asset ORDER BY total_pnl_pct DESC",
            params,
        )).fetchall()
    return [AssetPnl(**r) for r in rows]


def _live_price(asset: str) -> float:
    try:
        r = _requests.get(_BINANCE_TICKER, params={'symbol': f'{asset}USD'}, timeout=3)
        r.raise_for_status()
        return float(r.json()['price'])
    except Exception:
        return 0.0


async def fetch_portfolio(
    pool: psycopg_pool.AsyncConnectionPool,
) -> Portfolio:
    """
    Reconstruct open positions from live_trades: for each asset, find any BUY
    that hasn't been matched by a subsequent SELL.
    """
    async with pool.connection() as conn:
        rows = await (await conn.execute(
            "SELECT asset, side, price, coins, usd, ts "
            "FROM live_trades ORDER BY ts ASC"
        )).fetchall()

    # Group by asset, walk forward
    by_asset: dict[str, list] = {}
    for r in rows:
        by_asset.setdefault(r['asset'], []).append(r)

    positions: list[Position] = []
    total_invested = 0.0

    for asset, trades in by_asset.items():
        held_coins = 0.0
        entry_cost = 0.0
        entry_time = None
        for t in trades:
            if t['side'] == 'BUY':
                held_coins += float(t['coins'])
                entry_cost += float(t['usd'])
                if entry_time is None:
                    entry_time = t['ts']
            else:
                held_coins -= float(t['coins'])
                entry_cost  = 0.0
                entry_time  = None
                if held_coins < 0:
                    held_coins = 0.0

        if held_coins <= 0 or entry_cost <= 0:
            continue

        entry_price  = entry_cost / held_coins
        current      = _live_price(asset)
        market_value = held_coins * current * (1 - FEE_SELL)
        net_entry    = entry_price * (1 + FEE_BUY)
        pnl_pct      = (current * (1 - FEE_SELL) - net_entry) / net_entry * 100 if net_entry else 0.0

        positions.append(Position(
            asset               = asset,
            coins               = held_coins,
            entry_price         = entry_price,
            entry_time          = entry_time or datetime.datetime.now(datetime.timezone.utc),
            current_price       = current,
            market_value        = market_value,
            unrealized_pnl_pct  = round(pnl_pct, 4),
        ))
        total_invested += market_value

    # Cash: approximate from trade history (sum of sells minus sum of buys)
    async with pool.connection() as conn:
        cash_row = await (await conn.execute(
            "SELECT "
            "  COALESCE(SUM(usd) FILTER (WHERE side='SELL'), 0) - "
            "  COALESCE(SUM(usd) FILTER (WHERE side='BUY'),  0) AS net "
            "FROM live_trades"
        )).fetchone()
    cash = float(cash_row['net']) if cash_row else 0.0

    return Portfolio(
        cash      = round(cash, 2),
        invested  = round(total_invested, 2),
        total     = round(cash + total_invested, 2),
        positions = positions,
        as_of     = datetime.datetime.now(datetime.timezone.utc),
    )
