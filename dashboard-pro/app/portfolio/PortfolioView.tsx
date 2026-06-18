'use client'

import { useQuery } from '@apollo/client/react'
import { PORTFOLIO_QUERY, type Portfolio, type DustBalance } from '../../lib/queries'

const fmt = (n: number) =>
  `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

const pct = (n: number) => {
  const c = n >= 0 ? 'text-green-400' : 'text-red-400'
  return (
    <span className={c}>
      {n >= 0 ? '+' : ''}
      {n.toFixed(2)}%
    </span>
  )
}

export function PortfolioView({ initial }: { initial: Portfolio }) {
  const { data } = useQuery<{ portfolio: Portfolio }>(PORTFOLIO_QUERY, {
    pollInterval: 30_000,
    fetchPolicy: 'cache-and-network',
  })
  const portfolio = data?.portfolio ?? initial

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Cash', value: fmt(portfolio.cash) },
          { label: 'Invested', value: fmt(portfolio.invested) },
          { label: 'Total', value: fmt(portfolio.total) },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-800 rounded-xl p-5">
            <div className="text-slate-400 text-sm mb-1">{label}</div>
            <div className="text-2xl font-semibold text-white">{value}</div>
          </div>
        ))}
      </div>

      {portfolio.positions.length === 0 ? (
        <div className="text-slate-400 bg-slate-800 rounded-xl p-6 text-center">No open positions</div>
      ) : (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-700 text-sm font-medium text-slate-300">
            Open Positions ({portfolio.positions.length})
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                {['Asset', 'Coins', 'Entry', 'Current', 'Market Value', 'P&L'].map((h) => (
                  <th key={h} className="text-left px-5 py-3 font-normal">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.map((pos) => (
                <tr key={pos.asset} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-5 py-3 font-medium text-white">{pos.asset}</td>
                  <td className="px-5 py-3">{pos.coins.toFixed(4)}</td>
                  <td className="px-5 py-3">{fmt(pos.entryPrice)}</td>
                  <td className="px-5 py-3">{fmt(pos.currentPrice)}</td>
                  <td className="px-5 py-3">{fmt(pos.marketValue)}</td>
                  <td className="px-5 py-3">{pct(pos.unrealizedPnlPct)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-5 py-2 text-xs text-slate-500">
            As of {new Date(portfolio.asOf).toLocaleTimeString()}
          </div>
        </div>
      )}

      {portfolio.dust.length > 0 && (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-700 text-sm font-medium text-slate-300">
            Dust ({portfolio.dust.length})
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                {['Asset', 'Coins', 'Current', 'Value'].map((h) => (
                  <th key={h} className="text-left px-5 py-3 font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {portfolio.dust.map((d: DustBalance) => (
                <tr key={d.asset} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="px-5 py-3 font-medium text-white">{d.asset}</td>
                  <td className="px-5 py-3 text-slate-400">{d.coins.toFixed(6)}</td>
                  <td className="px-5 py-3 text-slate-400">{fmt(d.currentPrice)}</td>
                  <td className="px-5 py-3 text-slate-400">{fmt(d.marketValue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
