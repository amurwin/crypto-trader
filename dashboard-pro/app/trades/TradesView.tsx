'use client'

import { useState } from 'react'
import { useQuery } from '@apollo/client/react'
import { TRADES_QUERY, type Trade } from '../../lib/queries'

const fmt = (n: number) =>
  `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

export function TradesView({ initial }: { initial: Trade[] }) {
  const [asset, setAsset] = useState('')
  const [side, setSide] = useState<'' | 'BUY' | 'SELL'>('')
  const [limit, setLimit] = useState(50)

  const { data, loading } = useQuery<{ trades: Trade[] }>(TRADES_QUERY, {
    variables: { asset: asset || undefined, side: side || undefined, limit },
    fetchPolicy: 'cache-and-network',
  })

  const trades = data?.trades ?? initial

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <input
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500 w-28"
          placeholder="Asset (e.g. BTC)"
          value={asset}
          onChange={(e) => setAsset(e.target.value.toUpperCase())}
        />
        <select
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
          value={side}
          onChange={(e) => setSide(e.target.value as '' | 'BUY' | 'SELL')}
        >
          <option value="">All sides</option>
          <option value="BUY">BUY</option>
          <option value="SELL">SELL</option>
        </select>
        <select
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
        >
          {[25, 50, 100, 250].map((n) => (
            <option key={n} value={n}>
              {n} rows
            </option>
          ))}
        </select>
      </div>

      {loading && <div className="text-slate-400 text-sm">Refreshing…</div>}

      <div className="bg-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-700">
              {['Time', 'Asset', 'Side', 'Price', 'Qty', 'USD', 'P&L', 'Reason'].map((h) => (
                <th key={h} className="text-left px-4 py-3 font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => (
              <tr key={t.id} className="border-b border-slate-700/40 hover:bg-slate-700/20">
                <td className="px-4 py-2.5 text-slate-400 whitespace-nowrap">
                  {new Date(t.ts).toLocaleString()}
                </td>
                <td className="px-4 py-2.5 font-medium text-white">{t.asset}</td>
                <td className="px-4 py-2.5">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      t.side === 'BUY' ? 'bg-blue-900/60 text-blue-300' : 'bg-purple-900/60 text-purple-300'
                    }`}
                  >
                    {t.side}
                  </span>
                </td>
                <td className="px-4 py-2.5">{fmt(t.price)}</td>
                <td className="px-4 py-2.5">{t.coins.toFixed(4)}</td>
                <td className="px-4 py-2.5">{fmt(t.usd)}</td>
                <td className="px-4 py-2.5">
                  {t.pnlPct != null ? (
                    <span className={t.pnlPct >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {t.pnlPct >= 0 ? '+' : ''}
                      {t.pnlPct.toFixed(2)}%
                    </span>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-slate-400 text-xs">{t.reason ?? '—'}</td>
              </tr>
            ))}
            {trades.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-slate-500">
                  No trades
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
