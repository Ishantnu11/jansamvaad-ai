import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Phone, BarChart2, Settings, Mic, Activity
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import CallsPage from './pages/CallsPage'
import CallDetailPage from './pages/CallDetailPage'
import LiveCallPage from './pages/LiveCallPage'
import AnalyticsPage from './pages/AnalyticsPage'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/calls', icon: Phone, label: 'Calls' },
  { to: '/live', icon: Mic, label: 'Live Call' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
]

export default function App() {
  return (
    <div className="flex min-h-screen bg-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-saffron to-orange-600 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-white text-sm">JanSamvaad AI</p>
              <p className="text-xs text-slate-400 font-hindi">जनसंवाद AI</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'bg-saffron/20 text-saffron border border-saffron/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700">
          <p className="text-xs text-slate-500 text-center">
            🇮🇳 Hindi Voice Outreach Agent
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/calls" element={<CallsPage />} />
          <Route path="/calls/:callId" element={<CallDetailPage />} />
          <Route path="/live" element={<LiveCallPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
      </main>
    </div>
  )
}
