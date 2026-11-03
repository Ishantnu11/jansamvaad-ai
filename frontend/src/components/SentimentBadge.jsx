import React from 'react'

const SENTIMENT_CONFIG = {
  positive:   { emoji: '😊', label: 'Positive',   cls: 'bg-emerald-900 text-emerald-300' },
  satisfied:  { emoji: '😄', label: 'Satisfied',  cls: 'bg-green-900 text-green-300' },
  neutral:    { emoji: '😐', label: 'Neutral',    cls: 'bg-slate-700 text-slate-300' },
  negative:   { emoji: '😞', label: 'Negative',   cls: 'bg-orange-900 text-orange-300' },
  frustrated: { emoji: '😤', label: 'Frustrated', cls: 'bg-red-900 text-red-300' },
}

export default function SentimentBadge({ sentiment }) {
  const cfg = SENTIMENT_CONFIG[sentiment] ?? { emoji: '❓', label: sentiment, cls: 'bg-slate-700 text-slate-300' }
  return (
    <span className={`badge ${cfg.cls}`}>
      {cfg.emoji} {cfg.label}
    </span>
  )
}
