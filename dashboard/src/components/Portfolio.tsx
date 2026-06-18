import { useEffect, useState } from 'react'
import { api, type Portfolio as PortfolioData, type DustBalance } from '../api'

const fmt = (n: number) => `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const pct  = (n: number) => {
  const c = n >= 0 ? 'text-green-400' : 'text-red-400'
  return <span className={c}>{n >= 0 ? '+' : ''}{n.toFixed(2)}%</span>
}

export default function Portfolio() {
  const [data, setData]   = useState<PortfolioData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.portfolio()
      .then(setData)
      .catch(e => setError(e.message))
  }, [])

  if (error) return <div className="text-red-400 p-4">Error: {error}</div>
  if (!data)  return <div className="text-slate-400 p-4">Loading…</div>

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Cash',     value: fmt(data.cash) },
          { label: 'Invested', value: fmt(data.invested) },
          { label: 'Total',    value: fmt(data.total) },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 rounded-xl p-5">
            <div className="text-slate-400 text-sm mb-1">{label}</div>
            <div className="text-2xl font-semibold text-white">{value}</div>
          </div>
        ))}
      </div>

      {/* Positions table */}
      {data.positions.length === 0 ? (
        <div className="text-slate-400 bg-slate-800 rounded-xl p-6 text-center">No open positions</div>
      ) : (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-700 text-sm font-medium text-slate-300">
            Open Positions ({data.positions.length})
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                {['Asset', 'Coins', 'Entry', 'Current', 'Market Value', 'P&L'].map(h => (
                  <th key={h} className="text-left px-5 py-3 font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.positions.map(pos => (
                <tr key={pos.asset} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-5 py-3 font-medium text-white">{pos.asset}</td>
                  <td className="px-5 py-3">{pos.coins.toFixed(4)}</td>
                  <td className="px-5 py-3">{fmt(pos.entry_price)}</td>
                  <td className="px-5 py-3">{fmt(pos.current_price)}</td>
                  <td className="px-5 py-3">{fmt(pos.market_value)}</td>
                  <td className="px-5 py-3">{pct(pos.unrealized_pnl_pct)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-5 py-2 text-xs text-slate-500">
            As of {new Date(data.as_of).toLocaleTimeString()}
          </div>
        </div>
      )}

      {/* Dust table */}
      {data.dust.length > 0 && (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-700 text-sm font-medium text-slate-300">
            Dust ({data.dust.length})
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                {['Asset', 'Coins', 'Current', 'Value'].map(h => (
                  <th key={h} className="text-left px-5 py-3 font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.dust.map((d: DustBalance) => (
                <tr key={d.asset} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-5 py-3 font-medium text-white">{d.asset}</td>
                  <td className="px-5 py-3 text-slate-400">{d.coins.toFixed(6)}</td>
                  <td className="px-5 py-3 text-slate-400">{fmt(d.current_price)}</td>
                  <td className="px-5 py-3 text-slate-400">{fmt(d.market_value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
