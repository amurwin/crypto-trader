import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import Portfolio from './components/Portfolio'
import Trades from './components/Trades'
import PnlSummary from './components/PnlSummary'
import PriceChart from './components/PriceChart'

const TABS = [
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/trades',    label: 'Trades' },
  { href: '/pnl',       label: 'P&L' },
  { href: '/chart',     label: 'Chart' },
]

export default function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-200">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center gap-6">
        <div className="text-white font-semibold tracking-tight">Crypto Trader</div>
        <nav className="flex gap-1">
          {TABS.map(t => (
            <NavLink
              key={t.href}
              to={t.href}
              className={({ isActive }) =>
                `px-4 py-1.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              {t.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        <Routes>
          <Route path="/" element={<Navigate to="/portfolio" replace />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/trades"    element={<Trades />} />
          <Route path="/pnl"       element={<PnlSummary />} />
          <Route path="/chart"     element={<PriceChart />} />
        </Routes>
      </main>
    </div>
  )
}
