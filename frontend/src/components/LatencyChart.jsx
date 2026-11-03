import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

export default function LatencyChart({ turns = [] }) {
  const data = turns
    .filter(t => t.speaker === 'agent' && t.latency_ms)
    .map((t, i) => ({ turn: `T${i + 1}`, latency: t.latency_ms }))

  if (!data.length) {
    return <p className="text-slate-500 text-sm text-center py-8">No latency data available.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="turn" tick={{ fill: '#94a3b8', fontSize: 12 }} />
        <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} unit="ms" />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
          labelStyle={{ color: '#f1f5f9' }}
          itemStyle={{ color: '#fb923c' }}
        />
        <ReferenceLine y={500} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Target 500ms', fill: '#ef4444', fontSize: 11 }} />
        <Line type="monotone" dataKey="latency" stroke="#fb923c" strokeWidth={2} dot={{ fill: '#fb923c', r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
