"""
Kraken exchange adapter.
"""

from __future__ import annotations
import base64
import hashlib
import hmac
import math
import time
import urllib.parse

import requests

from .base import Exchange, OrderResult

BASE_URL = 'https://api.kraken.com'

_lot_step_cache: dict[str, float] = {}


def _fmt_qty(quantity: float, step: float) -> str:
    decimals = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    return f'{quantity:.{decimals}f}'


class Kraken(Exchange):

    def __init__(self, api_key: str, api_secret: str, dry_run: bool = False):
        self._api_key    = api_key
        self._api_secret = api_secret
        self._dry_run    = dry_run

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _sign(self, path: str, data: dict) -> str:
        """Kraken HMAC-SHA512 signature."""
        post_data = urllib.parse.urlencode(data)
        encoded   = (str(data['nonce']) + post_data).encode()
        message   = path.encode() + hashlib.sha256(encoded).digest()
        secret    = base64.b64decode(self._api_secret)
        sig       = hmac.new(secret, message, hashlib.sha512)
        return base64.b64encode(sig.digest()).decode()

    def _public_get(self, path: str, params: dict | None = None) -> dict:
        r = requests.get(f'{BASE_URL}{path}', params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get('error'):
            raise Exception(f'Kraken API error: {data["error"]}')
        return data['result']

    def _private_post(self, path: str, data: dict) -> dict:
        data['nonce'] = int(time.time() * 1000)
        sig = self._sign(path, data)
        r   = requests.post(
            f'{BASE_URL}{path}',
            data=data,
            headers={'API-Key': self._api_key, 'API-Sign': sig},
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()
        if result.get('error'):
            raise Exception(f'Kraken API error: {result["error"]}')
        return result['result']

    # ── Exchange interface ────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return 'kraken'

    def symbol_for(self, asset: str) -> str:
        return f'{asset}USD'

    def lot_step(self, asset: str) -> float:
        if asset in _lot_step_cache:
            return _lot_step_cache[asset]
        try:
            result = self._public_get('/0/public/AssetPairs', {'pair': self.symbol_for(asset)})
            info = next(iter(result.values()))
            step = 10 ** (-int(info['lot_decimals']))
        except Exception:
            step = 1.0
        _lot_step_cache[asset] = step
        return step

    def get_price(self, symbol: str) -> float:
        pair   = self.symbol_for(symbol)
        result = self._public_get('/0/public/Ticker', {'pair': pair})
        # result key is the pair name (may differ slightly); grab first value
        info = next(iter(result.values()))
        return float(info['c'][0])  # last trade closed price

    def get_order_book_asks(self, symbol: str, limit: int = 20) -> list[tuple[float, float]]:
        pair   = self.symbol_for(symbol)
        result = self._public_get('/0/public/Depth', {'pair': pair, 'count': limit})
        book   = next(iter(result.values()))
        return [(float(p), float(q)) for p, q, _ in book['asks']]

    def get_klines(self, symbol: str, limit: int, end_ms: int | None = None) -> list:
        """
        Returns bars in the same format as Binance:
        [open_ms, open, high, low, close, vol, ...]
        Kraken OHLC interval is in minutes; we use 5-min bars.
        Kraken returns up to 720 bars; `limit` is used to trim from the end.
        """
        pair   = self.symbol_for(symbol)
        params: dict = {'pair': pair, 'interval': 5}
        if end_ms:
            params['since'] = (end_ms // 1000) - (limit * 300)
        result = self._public_get('/0/public/OHLC', params)
        bars   = next(iter(v for k, v in result.items() if k != 'last'))
        # Kraken: [time_s, open, high, low, close, vwap, volume, count]
        # Convert to Binance-style: [open_ms, open, high, low, close, vol]
        converted = [
            [b[0] * 1000, b[1], b[2], b[3], b[4], b[6]]
            for b in bars
        ]
        if end_ms:
            converted = [b for b in converted if b[0] <= end_ms]
        return converted[-limit:]

    def get_balances(self) -> dict[str, float]:
        result = self._private_post('/0/private/Balance', {})
        balances: dict[str, float] = {}
        for raw_asset, qty in result.items():
            # Strip Kraken X/Z prefixes for single-char internal names
            asset = raw_asset
            if len(raw_asset) == 4 and raw_asset[0] in ('X', 'Z'):
                asset = raw_asset[1:]
            val = float(qty)
            if val > 0:
                balances[asset] = val
        return balances

    def get_recent_trades(self, symbol: str, limit: int = 100) -> list[dict]:
        """
        Returns trades in normalized format matching the base interface:
        {'isBuyer': bool, 'qty': str, 'quoteQty': str, 'price': str, 'time': int}
        """
        pair   = self.symbol_for(symbol)
        result = self._private_post('/0/private/TradesHistory', {'type': 'all'})
        trades = []
        for txid, t in result.get('trades', {}).items():
            if t.get('pair') != pair and t.get('pair') != symbol:
                continue
            qty   = float(t['vol'])
            price = float(t['price'])
            trades.append({
                'isBuyer':  t['type'] == 'buy',
                'qty':      t['vol'],
                'quoteQty': f'{qty * price:.8f}',
                'price':    t['price'],
                'time':     int(float(t['time']) * 1000),
            })
        trades.sort(key=lambda x: x['time'], reverse=True)
        return trades[:limit]

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

        result = self._private_post('/0/private/AddOrder', {
            'pair':      pair,
            'type':      'buy',
            'ordertype': 'limit',
            'price':     price_str,
            'volume':    qty_str,
            'timeinforce': 'IOC',
        })
        txids = result.get('txid', [])
        order_id = txids[0] if txids else ''

        # Query the order to get fill details
        if order_id:
            try:
                info = self._private_post('/0/private/QueryOrders', {'txid': order_id})
                od   = info.get(order_id, {})
                filled_qty   = float(od.get('vol_exec', 0))
                filled_quote = float(od.get('cost', 0))
                return OrderResult(filled_qty=filled_qty, filled_quote=filled_quote, order_id=order_id)
            except Exception:
                pass
        return OrderResult(filled_qty=0.0, filled_quote=0.0, order_id=order_id)

    def place_market_sell(self, symbol: str, qty: float, step: float) -> OrderResult:
        qty_str = _fmt_qty(qty, step)
        pair    = self.symbol_for(symbol)

        if self._dry_run:
            return OrderResult(filled_qty=qty, filled_quote=0.0, order_id='dry')

        result = self._private_post('/0/private/AddOrder', {
            'pair':      pair,
            'type':      'sell',
            'ordertype': 'market',
            'volume':    qty_str,
        })
        txids    = result.get('txid', [])
        order_id = txids[0] if txids else ''

        if order_id:
            try:
                info = self._private_post('/0/private/QueryOrders', {'txid': order_id})
                od   = info.get(order_id, {})
                filled_qty   = float(od.get('vol_exec', 0))
                filled_quote = float(od.get('cost', 0))
                return OrderResult(filled_qty=filled_qty, filled_quote=filled_quote, order_id=order_id)
            except Exception:
                pass
        return OrderResult(filled_qty=qty, filled_quote=0.0, order_id=order_id)
