"""
Data access layer — queries PostgreSQL and Binance public API.
Used by both REST routes and GraphQL resolvers.
"""

from __future__ import annotations
import datetime
import hashlib
import hmac
import json
import os
import time
import requests as _requests
import redis

import psycopg_pool

from api.models import OhlcvBar, Trade, Position, Portfolio, DustBalance, AssetPnl, Asset

FEE_BUY  = 0.0002
FEE_SELL = 0.0002
_BINANCE_BASE   = 'https://api.binance.us'
_BINANCE_TICKER = f'{_BINANCE_BASE}/api/v3/ticker/price'

_redis = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

_TTL_PRICE    = 30   # seconds — one price tick
_TTL_BALANCES = 10   # seconds — one realtime loop cycle
_TTL_TRADES   = 10   # seconds — one realtime loop cycle


def _cache_get(key: str) -> object | None:
    raw = _redis.get(key)
    return json.loads(raw) if raw is not None else None


def _cache_set(key: str, value: object, ttl: int) -> None:
    _redis.setex(key, ttl, json.dumps(value))


def _binance_signed_get(path: str, params: dict) -> dict | list:
    api_key    = os.environ['BINANCE_API_KEY']
    api_secret = os.environ['BINANCE_API_SECRET']
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 15000
    qs  = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    sig = hmac.new(api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    r   = _requests.get(
        f'{_BINANCE_BASE}{path}',
        params=qs + '&signature=' + sig,
        headers={'X-MBX-APIKEY': api_key},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def _binance_my_trades(symbol: str) -> list[dict]:
    """Fetch all trades for a symbol from Binance, paginating past the 1000-row limit."""
    cache_key = f'binance:trades:{symbol}'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    all_trades: list[dict] = []
    from_id: int | None = None
    while True:
        params: dict = {'symbol': symbol, 'limit': 1000}
        if from_id is not None:
            params['fromId'] = from_id
        batch = _binance_signed_get('/api/v3/myTrades', params)
        if not batch:
            break
        all_trades.extend(batch)
        if len(batch) < 1000:
            break
        from_id = batch[-1]['id'] + 1
    _cache_set(cache_key, all_trades, _TTL_TRADES)
    return all_trades


def _binance_balances() -> dict[str, float]:
    cached = _cache_get('binance:balances')
    if cached is not None:
        return cached
    data = _binance_signed_get('/api/v3/account', {})
    result = {
        b['asset']: float(b['free']) + float(b['locked'])
        for b in data['balances']
        if float(b['free']) + float(b['locked']) > 0
    }
    _cache_set('binance:balances', result, _TTL_BALANCES)
    return result


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
    since_ms = int(since.timestamp() * 1000) if since else None
    assets = await fetch_assets(pool)
    result: list[AssetPnl] = []

    for asset_obj in assets:
        symbol = f'{asset_obj.symbol}USD'
        try:
            trades = _binance_my_trades(symbol)
        except Exception:
            continue
        if not trades:
            continue

        # Walk all trades in time order to maintain an average cost basis,
        # then collect per-sell P&L.  Buys before 'since' still inform cost
        # basis so filtering is only applied to which sells we report.
        avg_cost  = 0.0
        held_qty  = 0.0
        pnl_list: list[float] = []

        for t in sorted(trades, key=lambda x: x['time']):
            qty       = float(t['qty'])
            quote_qty = float(t['quoteQty'])
            if t['isBuyer']:
                new_qty  = held_qty + qty
                avg_cost = (avg_cost * held_qty + quote_qty) / new_qty
                held_qty = new_qty
            else:
                if avg_cost > 0 and (since_ms is None or t['time'] >= since_ms):
                    sell_price = quote_qty / qty if qty else 0
                    pnl_list.append((sell_price - avg_cost) / avg_cost * 100)
                held_qty = max(0.0, held_qty - qty)

        if not pnl_list:
            continue

        wins  = sum(1 for p in pnl_list if p > 0)
        result.append(AssetPnl(
            asset         = asset_obj.symbol,
            trades        = len(pnl_list),
            wins          = wins,
            losses        = len(pnl_list) - wins,
            avg_pnl_pct   = round(sum(pnl_list) / len(pnl_list), 4),
            total_pnl_pct = round(sum(pnl_list), 4),
        ))

    return sorted(result, key=lambda x: x.total_pnl_pct, reverse=True)


def _live_price(asset: str) -> float:
    cache_key = f'binance:price:{asset}'
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        r = _requests.get(_BINANCE_TICKER, params={'symbol': f'{asset}USD'}, timeout=3)
        r.raise_for_status()
        price = float(r.json()['price'])
        _cache_set(cache_key, price, _TTL_PRICE)
        return price
    except Exception:
        return 0.0


async def fetch_portfolio(
    pool: psycopg_pool.AsyncConnectionPool,
) -> Portfolio:
    """
    Reconstruct open positions from live_trades: for each asset, find any BUY
    that hasn't been matched by a subsequent SELL.
    """
    binance = _binance_balances()
    cash = binance.get('USD', 0.0)

    async with pool.connection() as conn:
        rows = await (await conn.execute(
            "SELECT asset, side, price, coins, usd, ts "
            "FROM live_trades ORDER BY ts ASC"
        )).fetchall()

    # Group by asset, walk forward to get entry cost/time
    by_asset: dict[str, list] = {}
    for r in rows:
        by_asset.setdefault(r['asset'], []).append(r)

    positions: list[Position] = []
    dust: list[DustBalance]  = []
    total_invested = 0.0
    position_assets: set[str] = set()

    for asset, trades in by_asset.items():
        held_coins = binance.get(asset, 0.0)
        if held_coins <= 0:
            continue

        entry_cost = 0.0
        entry_time = None
        for t in trades:
            if t['side'] == 'BUY':
                entry_cost += float(t['usd'])
                if entry_time is None:
                    entry_time = t['ts']
            else:
                entry_cost = 0.0
                entry_time = None

        if entry_cost <= 0:
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
        position_assets.add(asset)

    for asset, held_coins in binance.items():
        if asset == 'USD' or asset in position_assets or held_coins <= 0:
            continue
        current      = _live_price(asset)
        market_value = held_coins * current
        dust.append(DustBalance(
            asset         = asset,
            coins         = held_coins,
            current_price = current,
            market_value  = round(market_value, 4),
        ))
        total_invested += market_value

    return Portfolio(
        cash      = round(cash, 2),
        invested  = round(total_invested, 2),
        total     = round(cash + total_invested, 2),
        positions = positions,
        dust      = sorted(dust, key=lambda d: d.market_value, reverse=True),
        as_of     = datetime.datetime.now(datetime.timezone.utc),
    )
