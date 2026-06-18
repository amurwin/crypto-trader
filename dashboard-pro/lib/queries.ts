import { gql } from '@apollo/client'

export interface OhlcvBar {
  ts: string
  open: number
  high: number
  low: number
  close: number
  vol: number
}

export interface Trade {
  id: number
  ts: string
  asset: string
  side: 'BUY' | 'SELL'
  price: number
  coins: number
  usd: number
  pnlPct: number | null
  reason: string | null
}

export interface Position {
  asset: string
  coins: number
  entryPrice: number
  entryTime: string
  currentPrice: number
  marketValue: number
  unrealizedPnlPct: number
}

export interface DustBalance {
  asset: string
  coins: number
  currentPrice: number
  marketValue: number
}

export interface Portfolio {
  cash: number
  invested: number
  total: number
  positions: Position[]
  dust: DustBalance[]
  asOf: string
}

export interface AssetPnl {
  asset: string
  trades: number
  wins: number
  losses: number
  avgPnlPct: number
  totalPnlPct: number
}

export interface Asset {
  symbol: string
  exchange: string
}

export const PORTFOLIO_QUERY = gql`
  query Portfolio {
    portfolio {
      cash
      invested
      total
      asOf
      positions {
        asset
        coins
        entryPrice
        entryTime
        currentPrice
        marketValue
        unrealizedPnlPct
      }
      dust {
        asset
        coins
        currentPrice
        marketValue
      }
    }
  }
`

export const TRADES_QUERY = gql`
  query Trades($asset: String, $side: String, $limit: Int) {
    trades(asset: $asset, side: $side, limit: $limit) {
      id
      ts
      asset
      side
      price
      coins
      usd
      pnlPct
      reason
    }
  }
`

export const PNL_QUERY = gql`
  query Pnl {
    pnl {
      asset
      trades
      wins
      losses
      avgPnlPct
      totalPnlPct
    }
  }
`

export const OHLCV_QUERY = gql`
  query Ohlcv($asset: String!, $limit: Int) {
    ohlcv(asset: $asset, limit: $limit) {
      ts
      open
      high
      low
      close
      vol
    }
  }
`

export const ASSETS_QUERY = gql`
  query Assets($exchange: String) {
    assets(exchange: $exchange) {
      symbol
      exchange
    }
  }
`
