import React from 'react'
import { Link } from 'react-router-dom'
import { Phone, CheckCircle, Clock, Zap, TrendingUp, AlertTriangle } from 'lucide-react'
import { useAnalytics } from '../hooks/useCallData'
import StatCard from '../components/StatCard'
import CallStatusBadge from '../components/CallStatusBadge'
import SentimentBadge from '../components/SentimentBadge'
import { format } from 'date-fns'

export default function Dashboard() {
  const { summary, recentCalls, loading, error } = useAnalytics()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-saffron border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 text-sm font-hindi mt-0.5">जनसंवाद AI — सर्वे अवलोकन</p>
        </div>
        <Link to="/live" className="btn-primary">
          <Phone className="w-4 h-4" />
          New Call
        </Link>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Backend unavailable — showing demo data. {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Phone}
          label="Total Calls"
          value={summary?.total_calls ?? 0}
          color="orange"
        />
        <StatCard
          icon={CheckCircle}
          label="Completed"
          value={summary?.completed_calls ?? 0}
          sub={`${summary?.total_calls ? Math.round((summary.completed_calls / summary.total_calls) * 100) : 0}% completion`}
          color="green"
        />
        <StatCard
          icon={Clock}
          label="Avg Duration"
          value={summary?.avg_duration ? `${Math.round(summary.avg_duration)}s` : '—'}
          color="blue"
        />
        <StatCard
          icon={Zap}
          label="Avg Latency"
          value={summary?.avg_latency ? `${Math.round(summary.avg_latency)}ms` : '—'}
          sub="response time"
          color="purple"
        />
      </div>

      {/* Sentiment breakdown */}
      {summary?.sentiment_breakdown && (
        <div className="card">
          <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-saffron" />
            Sentiment Breakdown
          </h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(summary.sentiment_breakdown).map(([sentiment, count]) => (
              <div key={sentiment} className="flex items-center gap-2">
                <SentimentBadge sentiment={sentiment} />
                <span className="text-white font-semibold text-sm">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent calls */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold">Recent Calls</h2>
          <Link to="/calls" className="text-saffron text-sm hover:underline">View all →</Link>
        </div>
        {recentCalls.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-6">No calls yet. Start your first call!</p>
        ) : (
          <div className="space-y-3">
            {recentCalls.map((call) => (
              <Link
                key={call.call_id}
                to={`/calls/${call.call_id}`}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-700/50 transition-colors border border-slate-700/50 group"
              >
                <div className="w-9 h-9 rounded-full bg-saffron/10 flex items-center justify-center text-saffron">
                  <Phone className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium text-sm truncate">
                    {call.citizen_name || call.phone_number || 'Unknown Citizen'}
                  </p>
                  <p className="text-slate-500 text-xs">
                    {call.created_at ? format(new Date(call.created_at), 'dd MMM yyyy, HH:mm') : '—'}
                    {call.duration_seconds ? ` · ${call.duration_seconds}s` : ''}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <CallStatusBadge status={call.status} />
                  {call.feedback?.citizen_sentiment && (
                    <SentimentBadge sentiment={call.feedback.citizen_sentiment} />
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
