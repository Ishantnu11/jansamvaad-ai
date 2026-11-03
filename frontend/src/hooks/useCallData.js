import { useState, useEffect, useCallback } from 'react'
import { getAnalyticsSummary, listCalls, getIssueBreakdown, getRecentCalls } from '../lib/api'

export function useAnalytics(refreshInterval = 30000) {
  const [summary, setSummary] = useState(null)
  const [issues, setIssues] = useState([])
  const [recentCalls, setRecentCalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    try {
      const [s, i, r] = await Promise.all([
        getAnalyticsSummary(),
        getIssueBreakdown(),
        getRecentCalls(5),
      ])
      setSummary(s.data)
      setIssues(i.data)
      setRecentCalls(r.data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, refreshInterval)
    return () => clearInterval(id)
  }, [fetchAll, refreshInterval])

  return { summary, issues, recentCalls, loading, error, refetch: fetchAll }
}

export function useCalls() {
  const [calls, setCalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async (params = {}) => {
    setLoading(true)
    try {
      const res = await listCalls(params)
      setCalls(res.data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetch() }, [fetch])
  return { calls, loading, error, refetch: fetch }
}
