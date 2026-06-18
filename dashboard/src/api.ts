const BASE = import.meta.env.VITE_API_URL ?? ''
const KEY  = import.meta.env.VITE_API_KEY  ?? ''

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(BASE + path, window.location.href)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) url.searchParams.set(k, String(v))
    }
  }
  const res = await fetch(url.toString(), {
    headers: { 'X-API-Key': KEY },
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export interface OhlcvBar {
  ts:    string
  open:  number
  high:  number
  low:   number
  close: number
  vol:   number
}

export interface Trade {
  id:      number
  ts:      string
  asset:   string
  side:    'BUY' | 'SELL'
  price:   number
  coins:   number
  usd:     number
  pnl_pct: number | null
  reason:  string | null
}

export interface Position {
  asset:               string
  coins:               number
  entry_price:         number
  entry_time:          string
  current_price:       number
  market_value:        number
  unrealized_pnl_pct:  number
}

export interface DustBalance {
  asset:         string
  coins:         number
  current_price: number
  market_value:  number
}

export interface Portfolio {
  cash:      number
  invested:  number
  total:     number
  positions: Position[]
  dust:      DustBalance[]
  as_of:     string
}

export interface AssetPnl {
  asset:         string
  trades:        number
  wins:          number
  losses:        number
  avg_pnl_pct:   number
  total_pnl_pct: number
}

export interface Asset {
  symbol:   string
  exchange: string
}

export const api = {
  assets:    (exchange?: string) => get<Asset[]>('/api/v1/assets', { exchange }),
  ohlcv:     (asset: string, limit = 200) => get<OhlcvBar[]>(`/api/v1/ohlcv/${asset}`, { limit }),
  trades:    (limit = 100, asset?: string) => get<Trade[]>('/api/v1/trades', { limit, asset }),
  pnl:       () => get<AssetPnl[]>('/api/v1/pnl'),
  portfolio: () => get<Portfolio>('/api/v1/portfolio'),
}
