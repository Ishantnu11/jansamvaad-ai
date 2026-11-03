import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Clock, Mic, Zap, MessageSquare } from 'lucide-react'
import { getCall } from '../lib/api'
import CallStatusBadge from '../components/CallStatusBadge'
import SentimentBadge from '../components/SentimentBadge'
import ConversationTimeline from '../components/ConversationTimeline'
import LatencyChart from '../components/LatencyChart'
import { format } from 'date-fns'

export default function CallDetailPage() {
  const { callId } = useParams()
  const [call, setCall] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCall(callId).then(r => { setCall(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [callId])

  if (loading) return (
    <div className="flex items-center justify-center h-full min-h-[400px]">
      <div className="w-8 h-8 border-2 border-saffron border-t-transparent rounded-full animate-spin" />
    </div>
  )
  if (!call) return (
    <div className="p-6 text-center text-slate-400">Call not found.</div>
  )

  return (
    <div className="p-6 space-y-6">
      {/* Back */}
      <Link to="/calls" className="flex items-center gap-2 text-slate-400 hover:text-white text-sm transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Calls
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {call.citizen_name || call.phone_number || 'Unknown Citizen'}
          </h1>
          <p className="text-slate-400 text-sm mt-1">Call ID: {call.call_id}</p>
          {call.created_at && (
            <p className="text-slate-500 text-xs">{format(new Date(call.created_at), 'dd MMMM yyyy, HH:mm:ss')}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <CallStatusBadge status={call.status} />
          {call.feedback?.citizen_sentiment && <SentimentBadge sentiment={call.feedback.citizen_sentiment} />}
        </div>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: Clock, label: 'Duration', value: call.duration_seconds ? `${call.duration_seconds}s` : '—' },
          { icon: MessageSquare, label: 'Turns', value: call.total_turns ?? 0 },
          { icon: Zap, label: 'Avg Latency', value: call.avg_latency_ms ? `${Math.round(call.avg_latency_ms)}ms` : '—' },
          { icon: Mic, label: 'Interruptions', value: call.interruptions ?? 0 },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="card text-center">
            <Icon className="w-5 h-5 text-saffron mx-auto mb-1" />
            <p className="text-white font-bold text-lg">{value}</p>
            <p className="text-slate-400 text-xs">{label}</p>
          </div>
        ))}
      </div>

      {/* Summary */}
      {call.summary && (
        <div className="card">
          <h2 className="text-white font-semibold mb-2">Call Summary</h2>
          <p className="text-slate-300 text-sm leading-relaxed font-hindi">{call.summary}</p>
        </div>
      )}

      {/* Feedback */}
      {call.feedback && (
        <div className="card">
          <h2 className="text-white font-semibold mb-3">Structured Feedback</h2>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(call.feedback).map(([k, v]) => (
              <div key={k} className="bg-slate-700/50 rounded-lg px-3 py-2">
                <p className="text-slate-400 text-xs capitalize">{k.replace(/_/g, ' ')}</p>
                <p className="text-white text-sm font-medium">{String(v ?? '—')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Latency chart */}
      {call.conversation?.length > 0 && (
        <div className="card">
          <h2 className="text-white font-semibold mb-3">Response Latency</h2>
          <LatencyChart turns={call.conversation} />
        </div>
      )}

      {/* Conversation */}
      <div className="card">
        <h2 className="text-white font-semibold mb-4">Conversation Transcript</h2>
        <ConversationTimeline turns={call.conversation ?? []} />
      </div>
    </div>
  )
}
