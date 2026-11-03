import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Calls ──────────────────────────────────────────────────────────────────
export const initiateCall = (data) => api.post('/api/calls/initiate', data)
export const sendTurn = (callId, data) => api.post(`/api/calls/${callId}/turn`, data)
export const getCall = (callId) => api.get(`/api/calls/${callId}`)
export const listCalls = (params) => api.get('/api/calls/', { params })
export const endCall = (callId) => api.post(`/api/calls/${callId}/end`)

// ── Analytics ─────────────────────────────────────────────────────────────
export const getAnalyticsSummary = () => api.get('/api/analytics/summary')
export const getRecentCalls = (limit = 10) => api.get('/api/analytics/recent', { params: { limit } })
export const getIssueBreakdown = () => api.get('/api/analytics/issues')

// ── LiveKit ───────────────────────────────────────────────────────────────
export const getLivekitToken = (room, participant = 'citizen') =>
  api.get('/api/livekit/token', { params: { room, participant } })

export default api
