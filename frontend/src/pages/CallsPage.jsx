import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Phone, Search, RefreshCw } from 'lucide-react'
import { useCalls } from '../hooks/useCallData'
import CallStatusBadge from '../components/CallStatusBadge'
import SentimentBadge from '../components/SentimentBadge'
import { format } from 'date-fns'

const STATUS_FILTERS = ['all', 'completed', 'in_progress', 'initiated', 'failed']

export default function CallsPage() {
  const { calls, loading, refetch } = useCalls()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const filtered = calls.filter(c => {
    const matchesSearch =
      (c.citizen_name || '').toLowerCase().includes(search.toLowerCase()) ||
      (c.phone_number || '').includes(search) ||
      c.call_id.includes(search)
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Call Records</h1>
          <p className="text-slate-400 text-sm">All outreach call history</p>
        </div>
        <div className="flex gap-2">
          <button onClick={refetch} className="btn-secondary">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <Link to="/live" className="btn-primary">
            <Phone className="w-4 h-4" />
            New Call
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by name, phone, or call ID..."
            className="w-full pl-9 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-saffron"
          />
        </div>
        <div className="flex gap-1 bg-slate-800 border border-slate-700 rounded-lg p-1">
          {STATUS_FILTERS.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors ${
                statusFilter === s
                  ? 'bg-saffron text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-saffron border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-12">No calls found.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                {['Citizen', 'Phone', 'Status', 'Duration', 'Sentiment', 'Date', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {filtered.map(call => (
                <tr key={call.call_id} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-4 py-3 text-sm text-white font-medium">
                    {call.citizen_name || '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">{call.phone_number || '—'}</td>
                  <td className="px-4 py-3"><CallStatusBadge status={call.status} /></td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {call.duration_seconds ? `${call.duration_seconds}s` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {call.feedback?.citizen_sentiment
                      ? <SentimentBadge sentiment={call.feedback.citizen_sentiment} />
                      : <span className="text-slate-600 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {call.created_at ? format(new Date(call.created_at), 'dd MMM, HH:mm') : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/calls/${call.call_id}`} className="text-saffron text-xs hover:underline">
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
