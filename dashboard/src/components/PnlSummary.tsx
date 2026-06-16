import { useEffect, useState } from 'react'
import { api, type AssetPnl } from '../api'

export default function PnlSummary() {
  const [rows, setRows]   = useState<AssetPnl[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.pnl().then(setRows).catch(e => setError(e.message))
  }, [])

  if (error) return <div className="text-red-400 p-4">Error: {error}</div>
  if (!rows.length) return <div className="text-slate-400 p-4">Loading…</div>

  const totalTrades = rows.reduce((s, r) => s + r.trades, 0)
  const totalWins   = rows.reduce((s, r) => s + r.wins, 0)
  const overallWinRate = totalTrades ? (totalWins / totalTrades * 100).toFixed(1) : '—'
  const combinedPnl = rows.reduce((s, r) => s + r.total_pnl_pct, 0)

  return (
    <div className="space-y-5">
      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Trades', value: totalTrades },
          { label: 'Win Rate',     value: `${overallWinRate}%` },
          { label: 'Combined P&L', value: <span className={combinedPnl >= 0 ? 'text-green-400' : 'text-red-400'}>{combinedPnl >= 0 ? '+' : ''}{combinedPnl.toFixed(2)}%</span> },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 rounded-xl p-5">
            <div className="text-slate-400 text-sm mb-1">{label}</div>
            <div className="text-2xl font-semibold text-white">{value}</div>
          </div>
        ))}
      </div>

      <div className="bg-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-700">
              {['Asset', 'Trades', 'Win Rate', 'Avg P&L', 'Total P&L'].map(h => (
                <th key={h} className="text-left px-5 py-3 font-normal">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => {
              const winRate = r.trades ? (r.wins / r.trades * 100).toFixed(0) : 0
              return (
                <tr key={r.asset} className="border-b border-slate-700/40 hover:bg-slate-700/20">
                  <td className="px-5 py-3 font-medium text-white">{r.asset}</td>
                  <td className="px-5 py-3">{r.trades}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full bg-green-500 rounded-full" style={{ width: `${winRate}%` }} />
                      </div>
                      <span>{winRate}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <span className={r.avg_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {r.avg_pnl_pct >= 0 ? '+' : ''}{r.avg_pnl_pct.toFixed(3)}%
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={r.total_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {r.total_pnl_pct >= 0 ? '+' : ''}{r.total_pnl_pct.toFixed(2)}%
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
