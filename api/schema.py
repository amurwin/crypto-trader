"""
GraphQL schema (Strawberry).
Mirrors REST endpoints; same auth, same data layer.
"""

from __future__ import annotations
import datetime
from typing import Optional, List

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from api.auth import require_api_key
from api.db import get_pool
from api import data
from api.models import (
    OhlcvBarGql, TradeGql, PositionGql, PortfolioGql, DustBalanceGql, AssetPnlGql, AssetGql,
    OhlcvBar, Trade, AssetPnl, Asset,
)


def _to_asset_gql(a: Asset) -> AssetGql:
    return AssetGql(symbol=a.symbol, exchange=a.exchange)


def _to_ohlcv_gql(b: OhlcvBar) -> OhlcvBarGql:
    return OhlcvBarGql(ts=b.ts, open=b.open, high=b.high, low=b.low, close=b.close, vol=b.vol)


def _to_trade_gql(t: Trade) -> TradeGql:
    return TradeGql(
        id=t.id, ts=t.ts, asset=t.asset, side=t.side,
        price=t.price, coins=t.coins, usd=t.usd,
        pnl_pct=t.pnl_pct, reason=t.reason,
    )


def _to_pnl_gql(p: AssetPnl) -> AssetPnlGql:
    return AssetPnlGql(
        asset=p.asset, trades=p.trades, wins=p.wins, losses=p.losses,
        avg_pnl_pct=p.avg_pnl_pct, total_pnl_pct=p.total_pnl_pct,
    )


@strawberry.type
class Query:

    @strawberry.field
    async def assets(self, info: Info, exchange: Optional[str] = None) -> List[AssetGql]:
        _check_auth(info)
        pool = await get_pool()
        rows = await data.fetch_assets(pool, exchange=exchange)
        return [_to_asset_gql(a) for a in rows]

    @strawberry.field
    async def ohlcv(
        self,
        info: Info,
        asset: str,
        limit: int = 200,
        start: Optional[datetime.datetime] = None,
        end:   Optional[datetime.datetime] = None,
    ) -> List[OhlcvBarGql]:
        _check_auth(info)
        pool = await get_pool()
        if not await data.asset_exists(pool, asset):
            raise ValueError(f'Unknown asset: {asset}')
        bars = await data.fetch_ohlcv(pool, asset, limit=limit, start=start, end=end)
        return [_to_ohlcv_gql(b) for b in bars]

    @strawberry.field
    async def trades(
        self,
        info:  Info,
        asset: Optional[str]              = None,
        side:  Optional[str]              = None,
        limit: int                        = 100,
        since: Optional[datetime.datetime] = None,
    ) -> List[TradeGql]:
        _check_auth(info)
        pool = await get_pool()
        trades = await data.fetch_trades(pool, asset=asset, side=side, limit=limit, since=since)
        return [_to_trade_gql(t) for t in trades]

    @strawberry.field
    async def pnl(
        self,
        info:  Info,
        since: Optional[datetime.datetime] = None,
    ) -> List[AssetPnlGql]:
        _check_auth(info)
        pool = await get_pool()
        rows = await data.fetch_pnl_summary(pool, since=since)
        return [_to_pnl_gql(r) for r in rows]

    @strawberry.field
    async def portfolio(self, info: Info) -> PortfolioGql:
        _check_auth(info)
        pool = await get_pool()
        p = await data.fetch_portfolio(pool)
        return PortfolioGql(
            cash=p.cash, invested=p.invested, total=p.total, as_of=p.as_of,
            positions=[
                PositionGql(
                    asset=pos.asset, coins=pos.coins, entry_price=pos.entry_price,
                    entry_time=pos.entry_time, current_price=pos.current_price,
                    market_value=pos.market_value, unrealized_pnl_pct=pos.unrealized_pnl_pct,
                )
                for pos in p.positions
            ],
            dust=[
                DustBalanceGql(
                    asset=d.asset, coins=d.coins,
                    current_price=d.current_price, market_value=d.market_value,
                )
                for d in p.dust
            ],
        )


def _check_auth(info: Info):
    request = info.context['request']
    key = request.headers.get('X-API-Key')
    require_api_key(key)


schema = strawberry.Schema(query=Query)

graphql_router = GraphQLRouter(schema, graphql_ide=None)
