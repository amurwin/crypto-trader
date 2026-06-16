"""
REST API routes.
All endpoints require X-API-Key header.
"""

from __future__ import annotations
import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, HTTPException

from api.auth import require_api_key
from api.db import get_pool
from api.models import OhlcvBar, Trade, Position, Portfolio, AssetPnl, Asset
from api import data

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get('/assets', response_model=list[Asset])
async def get_assets(exchange: Optional[str] = None):
    """List of tradeable assets, optionally filtered by exchange."""
    pool = await get_pool()
    return await data.fetch_assets(pool, exchange=exchange)


@router.get('/ohlcv/{asset}', response_model=list[OhlcvBar])
async def get_ohlcv(
    asset:  str,
    limit:  Annotated[int, Query(ge=1, le=10000)] = 200,
    start:  Optional[datetime.datetime] = None,
    end:    Optional[datetime.datetime] = None,
):
    """Historical 5-minute OHLCV bars for a given asset symbol."""
    pool = await get_pool()
    if not await data.asset_exists(pool, asset):
        raise HTTPException(status_code=404, detail=f'Unknown asset: {asset}')
    return await data.fetch_ohlcv(pool, asset, limit=limit, start=start, end=end)


@router.get('/trades', response_model=list[Trade])
async def get_trades(
    asset:  Optional[str]              = None,
    side:   Optional[str]              = None,
    limit:  Annotated[int, Query(ge=1, le=1000)] = 100,
    since:  Optional[datetime.datetime] = None,
):
    """Recent live trades. Filter by asset, side (BUY/SELL), or date."""
    pool = await get_pool()
    return await data.fetch_trades(pool, asset=asset, side=side, limit=limit, since=since)


@router.get('/pnl', response_model=list[AssetPnl])
async def get_pnl(
    since: Optional[datetime.datetime] = None,
):
    """P&L summary by asset (sell trades only)."""
    pool = await get_pool()
    return await data.fetch_pnl_summary(pool, since=since)


@router.get('/portfolio', response_model=Portfolio)
async def get_portfolio():
    """Open positions with live prices and unrealized P&L, plus estimated cash."""
    pool = await get_pool()
    return await data.fetch_portfolio(pool)
