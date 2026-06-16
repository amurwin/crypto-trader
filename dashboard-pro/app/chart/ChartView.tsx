'use client'

import { useState } from 'react'
import { useQuery } from '@apollo/client/react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { OHLCV_QUERY, ASSETS_QUERY, type OhlcvBar, type Asset } from '../../lib/queries'

const LIMITS = [48, 288, 1008, 2016, 4032]
const LIMIT_LABELS: Record<number, string> = {
  48: '4 h', 288: '1 d', 1008: '3.5 d', 2016: '1 w', 4032: '2 w',
}

function fmtTime(ts: number, limit: number) {
  const d = new Date(ts)
  if (limit <= 288) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

export function ChartView({
  initial,
  initialAsset,
  initialAssets,
}: {
  initial: OhlcvBar[]
  initialAsset: string
  initialAssets: Asset[]
}) {
  const [asset, setAsset] = useState(initialAsset)
  const [limit, setLimit] = useState(288)

  const { data: assetsData } = useQuery<{ assets: Asset[] }>(ASSETS_QUERY, {
    fetchPolicy: 'cache-and-network',
  })
  const assets = assetsData?.assets ?? initialAssets

  const { data, loading } = useQuery<{ ohlcv: OhlcvBar[] }>(OHLCV_QUERY, {
    variables: { asset, limit },
    fetchPolicy: 'cache-and-network',
  })

  const bars = (asset === initialAsset && limit === 288 ? data?.ohlcv ?? initial : data?.ohlcv ?? []).map((b) => ({
    ts: new Date(b.ts).getTime(),
    close: b.close,
  }))

  const first = bars[0]?.close ?? 0
  const last = bars[bars.length - 1]?.close ?? 0
  const change = first ? ((last - first) / first) * 100 : 0
  const color = change >= 0 ? '#4ade80' : '#f87171'

  return (
    <div className="space-y-4">
      <div className="flex gap-3 items-center flex-wrap">
        <select
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
          value={asset}
          onChange={(e) => setAsset(e.target.value)}
        >
          {assets.map((a) => (
            <option key={a.symbol} value={a.symbol}>
              {a.symbol}
            </option>
          ))}
        </select>
        <div className="flex gap-1">
          {LIMITS.map((l) => (
            <button
              key={l}
              onClick={() => setLimit(l)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                limit === l ? 'bg-slate-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {LIMIT_LABELS[l]}
            </button>
          ))}
        </div>
        {!loading && bars.length > 0 && (
          <div className="ml-auto text-right">
            <div className="text-xl font-semibold text-white">${last.toFixed(4)}</div>
            <div className={`text-sm ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {change >= 0 ? '+' : ''}
              {change.toFixed(2)}%
            </div>
          </div>
        )}
      </div>

      {bars.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-4">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={bars} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="ts"
                tickFormatter={(ts) => fmtTime(ts, limit)}
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                interval="preserveStartEnd"
                minTickGap={60}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `$${Number(v).toPrecision(4)}`}
                domain={['auto', 'auto']}
                width={72}
              />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelFormatter={(ts) => new Date(ts).toLocaleString()}
                formatter={(v) => [`$${Number(v).toFixed(6)}`, 'Close']}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke={color}
                strokeWidth={1.5}
                fill="url(#grad)"
                dot={false}
                activeDot={{ r: 4, fill: color }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
