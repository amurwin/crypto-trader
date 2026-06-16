import { useState } from 'react'
import Portfolio from './components/Portfolio'
import Trades from './components/Trades'
import PnlSummary from './components/PnlSummary'
import PriceChart from './components/PriceChart'

const TABS = ['Portfolio', 'Trades', 'P&L', 'Chart'] as const
type Tab = typeof TABS[number]

export default function App() {
  const [tab, setTab] = useState<Tab>('Portfolio')

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4 flex items-center gap-6">
        <div className="text-white font-semibold tracking-tight">Crypto Trader</div>
        <nav className="flex gap-1">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm transition-colors ${
                tab === t
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      {/* Content */}
      <main className="max-w-6xl mx-auto px-6 py-6">
        {tab === 'Portfolio' && <Portfolio />}
        {tab === 'Trades'    && <Trades />}
        {tab === 'P&L'       && <PnlSummary />}
        {tab === 'Chart'     && <PriceChart />}
      </main>
    </div>
  )
}
