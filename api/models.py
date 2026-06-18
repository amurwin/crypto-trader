"""
Shared data models — Pydantic for REST, Strawberry for GraphQL.
"""

from __future__ import annotations
import strawberry
from pydantic import BaseModel
from typing import Optional
import datetime


# ── OHLCV ─────────────────────────────────────────────────────────────────────

class OhlcvBar(BaseModel):
    ts:    datetime.datetime
    open:  float
    high:  float
    low:   float
    close: float
    vol:   float


@strawberry.type
class OhlcvBarGql:
    ts:    datetime.datetime
    open:  float
    high:  float
    low:   float
    close: float
    vol:   float


# ── Trades ────────────────────────────────────────────────────────────────────

class Trade(BaseModel):
    id:      int
    ts:      datetime.datetime
    asset:   str
    side:    str
    price:   float
    coins:   float
    usd:     float
    pnl_pct: Optional[float] = None
    reason:  Optional[str]   = None


@strawberry.type
class TradeGql:
    id:      int
    ts:      datetime.datetime
    asset:   str
    side:    str
    price:   float
    coins:   float
    usd:     float
    pnl_pct: Optional[float] = strawberry.UNSET
    reason:  Optional[str]   = strawberry.UNSET


# ── Positions ─────────────────────────────────────────────────────────────────

class Position(BaseModel):
    asset:        str
    coins:        float
    entry_price:  float
    entry_time:   datetime.datetime
    current_price: float
    market_value: float
    unrealized_pnl_pct: float


@strawberry.type
class PositionGql:
    asset:               str
    coins:               float
    entry_price:         float
    entry_time:          datetime.datetime
    current_price:       float
    market_value:        float
    unrealized_pnl_pct:  float


# ── Dust ──────────────────────────────────────────────────────────────────────

class DustBalance(BaseModel):
    asset:         str
    coins:         float
    current_price: float
    market_value:  float


@strawberry.type
class DustBalanceGql:
    asset:         str
    coins:         float
    current_price: float
    market_value:  float


# ── Portfolio ─────────────────────────────────────────────────────────────────

class Portfolio(BaseModel):
    cash:           float
    invested:       float
    total:          float
    positions:      list[Position]
    dust:           list[DustBalance]
    as_of:          datetime.datetime


@strawberry.type
class PortfolioGql:
    cash:       float
    invested:   float
    total:      float
    positions:  list[PositionGql]
    dust:       list[DustBalanceGql]
    as_of:      datetime.datetime


# ── Assets ────────────────────────────────────────────────────────────────────

class Asset(BaseModel):
    symbol:   str
    exchange: str


@strawberry.type
class AssetGql:
    symbol:   str
    exchange: str


# ── P&L summary ───────────────────────────────────────────────────────────────

class AssetPnl(BaseModel):
    asset:         str
    trades:        int
    wins:          int
    losses:        int
    avg_pnl_pct:   float
    total_pnl_pct: float


@strawberry.type
class AssetPnlGql:
    asset:         str
    trades:        int
    wins:          int
    losses:        int
    avg_pnl_pct:   float
    total_pnl_pct: float
