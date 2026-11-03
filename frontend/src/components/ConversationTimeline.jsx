import React from 'react'
import { Bot, User } from 'lucide-react'
import { format } from 'date-fns'
import SentimentBadge from './SentimentBadge'

export default function ConversationTimeline({ turns = [] }) {
  if (!turns.length) {
    return <p className="text-slate-500 text-sm text-center py-8">No conversation data available.</p>
  }
  return (
    <div className="space-y-4">
      {turns.map((turn, idx) => {
        const isAgent = turn.speaker === 'agent'
        return (
          <div key={idx} className={`flex gap-3 ${isAgent ? '' : 'flex-row-reverse'}`}>
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              isAgent ? 'bg-saffron/20 text-saffron' : 'bg-blue-900 text-blue-300'
            }`}>
              {isAgent ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
            </div>
            {/* Bubble */}
            <div className={`max-w-[75%] ${isAgent ? '' : 'items-end'} flex flex-col gap-1`}>
              <div className={`flex items-center gap-2 ${isAgent ? '' : 'flex-row-reverse'}`}>
                <span className="text-xs font-semibold text-slate-400">
                  {isAgent ? 'JanSamvaad AI' : 'Citizen'}
                </span>
                {turn.timestamp && (
                  <span className="text-xs text-slate-600">
                    {format(new Date(turn.timestamp), 'HH:mm:ss')}
                  </span>
                )}
                {turn.latency_ms && (
                  <span className="text-xs text-slate-600">⚡{turn.latency_ms}ms</span>
                )}
              </div>
              <div className={`rounded-2xl px-4 py-2.5 text-sm font-hindi leading-relaxed ${
                isAgent
                  ? 'bg-saffron/10 border border-saffron/20 text-slate-100'
                  : 'bg-slate-700 border border-slate-600 text-slate-200'
              }`}>
                {turn.text}
              </div>
              {turn.sentiment && !isAgent && (
                <div className={isAgent ? '' : 'self-end'}>
                  <SentimentBadge sentiment={turn.sentiment} />
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
