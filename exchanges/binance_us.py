"""
Binance.US exchange adapter.
"""

from __future__ import annotations
import hashlib
import hmac
import math
import os
import time

import requests

from .base import Exchange, OrderResult

BASE_URL = 'https://api.binance.us'

_lot_step_cache: dict[str, float] = {}


def _fmt_qty(quantity: float, step: float) -> str:
    decimals = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    return f'{quantity:.{decimals}f}'


class BinanceUS(Exchange):

    def __init__(self, api_key: str, api_secret: str, dry_run: bool = False):
        self._api_key    = api_key
        self._api_secret = api_secret
        self._dry_run    = dry_run

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _headers(self) -> dict:
        return {'X-MBX-APIKEY': self._api_key}

    def _signed_get(self, path: str, params: dict) -> dict:
        params['timestamp']  = int(time.time() * 1000)
        params['recvWindow'] = 15000
        qs  = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        sig = hmac.new(self._api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        r   = requests.get(f'{BASE_URL}{path}',
                           params=qs + '&signature=' + sig,
                           headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    def _signed_post(self, path: str, body: str) -> dict:
        sig = hmac.new(self._api_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        r   = requests.post(f'{BASE_URL}{path}',
                            data=body + '&signature=' + sig,
                            headers={**self._headers(),
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                            timeout=10)
        if not r.ok:
            raise Exception(f"{r.status_code} {r.reason}: {r.text}")
        return r.json()

    # ── Exchange interface ────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return 'binance_us'

    def symbol_for(self, asset: str) -> str:
        return f'{asset}USD'

    def lot_step(self, asset: str) -> float:
        if asset in _lot_step_cache:
            return _lot_step_cache[asset]
        try:
            r = requests.get(f'{BASE_URL}/api/v3/exchangeInfo',
                             params={'symbol': self.symbol_for(asset)}, timeout=5)
            r.raise_for_status()
            filters = r.json()['symbols'][0]['filters']
            step = next(float(f['stepSize']) for f in filters if f['filterType'] == 'LOT_SIZE')
        except Exception:
            step = 1.0
        _lot_step_cache[asset] = step
        return step

    def get_price(self, symbol: str) -> float:
        r = requests.get(f'{BASE_URL}/api/v3/ticker/price',
                         params={'symbol': self.symbol_for(symbol)}, timeout=5)
        r.raise_for_status()
        return float(r.json()['price'])

    def get_order_book_asks(self, symbol: str, limit: int = 20) -> list[tuple[float, float]]:
        r = requests.get(f'{BASE_URL}/api/v3/depth',
                         params={'symbol': self.symbol_for(symbol), 'limit': limit}, timeout=5)
        r.raise_for_status()
        return [(float(p), float(q)) for p, q in r.json()['asks']]

    def get_klines(self, symbol: str, limit: int, end_ms: int | None = None) -> list:
        params = {'symbol': self.symbol_for(symbol), 'interval': '5m', 'limit': limit}
        if end_ms:
            params['endTime'] = end_ms
        r = requests.get(f'{BASE_URL}/api/v3/klines', params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_balances(self) -> dict[str, float]:
        account = self._signed_get('/api/v3/account', {})
        return {b['asset']: float(b['free']) + float(b['locked'])
                for b in account['balances']
                if float(b['free']) + float(b['locked']) > 0}

    def get_recent_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        return self._signed_get('/api/v3/myTrades',
                                {'symbol': self.symbol_for(symbol), 'limit': limit})

    def place_limit_buy_ioc(self, symbol: str, usd_amount: float,
                             price_cap: float, step: float) -> OrderResult:
        qty     = math.floor(usd_amount / price_cap / step) * step
        if qty < step:
            raise Exception(f"Computed qty {qty} below min lot size {step}")
        qty_str   = _fmt_qty(qty, step)
        price_str = f'{price_cap:.8f}'.rstrip('0').rstrip('.')
        pair      = self.symbol_for(symbol)

        if self._dry_run:
            return OrderResult(filled_qty=qty, filled_quote=qty * price_cap, order_id='dry')

        ts   = int(time.time() * 1000)
        body = (f'symbol={pair}&side=BUY&type=LIMIT&timeInForce=IOC'
                f'&quantity={qty_str}&price={price_str}&timestamp={ts}&recvWindow=15000')
        res  = self._signed_post('/api/v3/order', body)
        return OrderResult(
            filled_qty   = float(res.get('executedQty') or 0),
            filled_quote = float(res.get('cummulativeQuoteQty') or 0),
            order_id     = str(res.get('orderId', '')),
        )

    def place_market_sell(self, symbol: str, qty: float, step: float) -> OrderResult:
        qty_str = _fmt_qty(qty, step)
        pair    = self.symbol_for(symbol)

        if self._dry_run:
            return OrderResult(filled_qty=qty, filled_quote=0.0, order_id='dry')

        ts   = int(time.time() * 1000)
        body = (f'symbol={pair}&side=SELL&type=MARKET'
                f'&quantity={qty_str}&timestamp={ts}&recvWindow=15000')
        res  = self._signed_post('/api/v3/order', body)
        return OrderResult(
            filled_qty   = float(res.get('executedQty') or 0),
            filled_quote = float(res.get('cummulativeQuoteQty') or 0),
            order_id     = str(res.get('orderId', '')),
        )
