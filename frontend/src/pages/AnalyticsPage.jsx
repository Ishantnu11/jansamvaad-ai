import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { useAnalytics } from '../hooks/useCallData'
import { TrendingUp, AlertTriangle } from 'lucide-react'

const COLORS = ['#FF6B2B', '#138808', '#3b82f6', '#a855f7', '#ec4899', '#06b6d4']

const SEVERITY_COLORS = {
  high:   '#ef4444',
  medium: '#f59e0b',
  low:    '#22c55e',
}

export default function AnalyticsPage() {
  const { summary, issues, loading, error } = useAnalytics()

  const sentimentData = summary?.sentiment_breakdown
    ? Object.entries(summary.sentiment_breakdown).map(([name, value]) => ({ name, value }))
    : []

  const categoryData = summary?.top_categories ?? []

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-slate-400 text-sm">Survey insights and call performance</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-yellow-900/30 border border-yellow-700 rounded-lg text-yellow-300 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Using cached/demo data — {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-saffron border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sentiment Pie */}
          <div className="card">
            <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-saffron" />
              Citizen Sentiment
            </h2>
            {sentimentData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={sentimentData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value}`}>
                    {sentimentData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-500 text-sm text-center py-16">No sentiment data yet.</p>
            )}
          </div>

          {/* Category Bar */}
          <div className="card">
            <h2 className="text-white font-semibold mb-4">Top Issue Categories</h2>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={categoryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis dataKey="category" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={120} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                  <Bar dataKey="count" fill="#FF6B2B" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-500 text-sm text-center py-16">No category data yet.</p>
            )}
          </div>

          {/* Issue breakdown table */}
          {issues.length > 0 && (
            <div className="card lg:col-span-2">
              <h2 className="text-white font-semibold mb-4">Issue Detail Breakdown</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      {['Category', 'Severity', 'Count', 'Avg Duration'].map(h => (
                        <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-slate-400 uppercase">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {issues.map((issue, i) => (
                      <tr key={i} className="hover:bg-slate-700/30">
                        <td className="px-3 py-2.5 text-white capitalize">{issue.category}</td>
                        <td className="px-3 py-2.5">
                          <span className="badge" style={{
                            backgroundColor: SEVERITY_COLORS[issue.severity] + '30',
                            color: SEVERITY_COLORS[issue.severity],
                          }}>
                            {issue.severity}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 text-white font-semibold">{issue.count}</td>
                        <td className="px-3 py-2.5 text-slate-400">
                          {issue.avg_duration_seconds ? `${Math.round(issue.avg_duration_seconds)}s` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
