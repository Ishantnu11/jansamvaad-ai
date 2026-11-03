import React from 'react'
import clsx from 'clsx'

export default function StatCard({ icon: Icon, label, value, sub, color = 'orange', trend }) {
  const colorMap = {
    orange: 'from-orange-500 to-saffron',
    green:  'from-emerald-500 to-green-600',
    blue:   'from-blue-500 to-indigo-600',
    purple: 'from-purple-500 to-violet-600',
    red:    'from-red-500 to-rose-600',
  }
  return (
    <div className="card flex items-start gap-4">
      <div className={clsx('w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center flex-shrink-0', colorMap[color])}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">{label}</p>
        <p className="text-white text-2xl font-bold mt-0.5">{value ?? '—'}</p>
        {sub && <p className="text-slate-500 text-xs mt-0.5">{sub}</p>}
        {trend !== undefined && (
          <p className={clsx('text-xs mt-1', trend >= 0 ? 'text-emerald-400' : 'text-red-400')}>
            {trend >= 0 ? '▲' : '▼'} {Math.abs(trend)}%
          </p>
        )}
      </div>
    </div>
  )
}
