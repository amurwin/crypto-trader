"""
Abstract exchange interface. All exchange adapters must implement this.

Each method raises NotImplementedError if not overridden.
Concrete implementations: BinanceUS, Kraken.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OrderResult:
    filled_qty:   float   # base asset quantity filled
    filled_quote: float   # USD spent / received
    order_id:     str


class Exchange(ABC):

    # ── Market data ───────────────────────────────────────────────────────────

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        """Current best price for symbol (e.g. 'LTC')."""

    @abstractmethod
    def get_order_book_asks(self, symbol: str, limit: int = 20) -> list[tuple[float, float]]:
        """Top `limit` ask levels as [(price, qty), ...]."""

    @abstractmethod
    def get_klines(self, symbol: str, limit: int, end_ms: int | None = None) -> list:
        """
        Recent 5-minute OHLCV bars.
        Returns list of [open_ms, open, high, low, close, vol, ...].
        """

    # ── Account ───────────────────────────────────────────────────────────────

    @abstractmethod
    def get_balances(self) -> dict[str, float]:
        """Free + locked balances. Returns {'USD': x, 'LTC': y, ...}."""

    @abstractmethod
    def get_recent_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        """
        Recent trades for symbol. Each dict must contain:
          'isBuyer' (bool), 'qty' (str), 'quoteQty' (str),
          'price' (str), 'time' (int ms).
        """

    # ── Orders ────────────────────────────────────────────────────────────────

    @abstractmethod
    def place_limit_buy_ioc(self, symbol: str, usd_amount: float,
                             price_cap: float, step: float) -> OrderResult:
        """
        IOC limit buy for up to `usd_amount` USD at or below `price_cap`.
        Returns what actually filled.
        """

    @abstractmethod
    def place_market_sell(self, symbol: str, qty: float, step: float) -> OrderResult:
        """Market sell `qty` of symbol."""

    # ── Exchange metadata ─────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable exchange name, e.g. 'binance_us' or 'kraken'."""

    @abstractmethod
    def symbol_for(self, asset: str) -> str:
        """
        Convert generic asset name (e.g. 'LTC') to exchange-specific
        trading pair string (e.g. 'LTCUSD' or 'XLTCZUSD').
        """

    @abstractmethod
    def lot_step(self, asset: str) -> float:
        """Minimum quantity increment for this asset on this exchange."""
