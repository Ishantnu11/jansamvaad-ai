import React from 'react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  completed:   { label: 'Completed',   cls: 'badge-green' },
  in_progress: { label: 'In Progress', cls: 'badge-blue' },
  initiated:   { label: 'Initiated',   cls: 'badge-yellow' },
  failed:      { label: 'Failed',      cls: 'badge-red' },
  no_answer:   { label: 'No Answer',   cls: 'badge-yellow' },
}

export default function CallStatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, cls: 'badge bg-slate-700 text-slate-300' }
  return <span className={clsx('badge', cfg.cls)}>{cfg.label}</span>
}
