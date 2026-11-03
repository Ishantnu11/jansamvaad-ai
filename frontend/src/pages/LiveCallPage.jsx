import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Phone, PhoneOff, Mic, MicOff, Loader2, Send, Volume2, CheckCircle2, Globe } from 'lucide-react'
import { initiateCall, sendTurn, endCall } from '../lib/api'

const SURVEY_TOPICS = [
  { value: 'public_services', label: 'Public Services (सार्वजनिक सुविधाएं)' },
  { value: 'water_supply', label: 'Water Supply (पानी)' },
  { value: 'roads', label: 'Roads & Infrastructure (सड़क)' },
  { value: 'electricity', label: 'Electricity (बिजली)' },
  { value: 'health', label: 'Healthcare (स्वास्थ्य)' },
  { value: 'education', label: 'Education (शिक्षा)' },
]

export default function LiveCallPage() {
  const [callMode, setCallMode] = useState('web')
  const [form, setForm] = useState({ citizen_name: '', phone_number: '+919991317827', survey_topic: 'public_services' })
  const [callState, setCallState] = useState('idle') // idle | connecting | active | ended
  const [agentStatus, setAgentStatus] = useState('idle') // idle | speaking | listening | thinking
  const [activeCall, setActiveCall] = useState(null)
  const [displayedTurns, setDisplayedTurns] = useState([])
  const [textInput, setTextInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [summaryData, setSummaryData] = useState(null)
  const [error, setError] = useState('')
  const [isSending, setIsSending] = useState(false)

  const recognitionRef = useRef(null)
  const audioRef = useRef(null)
  const turnsEndRef = useRef(null)
  const activeCallRef = useRef(null)
  const isSendingRef = useRef(false)

  // Keep ref in sync with state
  useEffect(() => { activeCallRef.current = activeCall }, [activeCall])
  useEffect(() => { isSendingRef.current = isSending }, [isSending])

  const scrollToBottom = () => {
    turnsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => { scrollToBottom() }, [displayedTurns])

  // Play audio from base64 string
  const playAudio = useCallback((base64Audio) => {
    if (!base64Audio) return Promise.resolve()
    return new Promise((resolve) => {
      try {
        if (audioRef.current) {
          audioRef.current.pause()
          audioRef.current = null
        }
        const audio = new Audio(`data:audio/wav;base64,${base64Audio}`)
        audioRef.current = audio
        setAgentStatus('speaking')
        audio.onended = () => {
          setAgentStatus('listening')
          resolve()
        }
        audio.onerror = () => {
          setAgentStatus('listening')
          resolve()
        }
        audio.play().catch(() => {
          setAgentStatus('listening')
          resolve()
        })
      } catch (err) {
        setAgentStatus('listening')
        resolve()
      }
    })
  }, [])

  // Start Browser Speech Recognition
  const doStartListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Browser speech recognition not supported. Use Chrome or type your answer.')
      return
    }

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort() } catch (_) {}
      }

      const recognition = new SpeechRecognition()
      recognition.lang = 'hi-IN'
      recognition.interimResults = false
      recognition.maxAlternatives = 1
      recognition.continuous = false

      recognition.onstart = () => {
        setIsListening(true)
        setAgentStatus('listening')
      }

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        if (transcript && transcript.trim()) {
          // Use a custom event so we avoid stale closures
          window.dispatchEvent(new CustomEvent('jansamvaad-speech', { detail: transcript.trim() }))
        }
      }

      recognition.onerror = (e) => {
        setIsListening(false)
        if (e.error === 'not-allowed') {
          setError('Microphone blocked. Click the lock icon near URL bar and allow Microphone.')
        } else if (e.error !== 'no-speech' && e.error !== 'aborted') {
          console.warn('Speech recognition notice:', e.error)
        }
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = recognition
      recognition.start()
    } catch (err) {
      console.warn('Speech recognition error:', err)
      setIsListening(false)
    }
  }, [])

  const doStopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch (_) {}
    }
    setIsListening(false)
  }, [])

  // Send citizen message to backend - the core flow
  const handleCitizenMessage = useCallback(async (messageText) => {
    if (!messageText) return
    const call = activeCallRef.current
    if (!call) {
      console.error('No active call')
      setError('No active call. Please start a call first.')
      return
    }
    if (isSendingRef.current) {
      console.warn('Already sending a turn, ignoring duplicate')
      return
    }

    doStopListening()
    setIsSending(true)
    setAgentStatus('thinking')
    setError('')

    // Add user turn immediately to UI
    setDisplayedTurns((prev) => [...prev, { speaker: 'citizen', text: messageText }])
    setTextInput('')

    try {
      console.log('Sending turn to backend:', call.call_id, messageText)
      const res = await sendTurn(call.call_id, { text: messageText })
      console.log('Got response from backend:', res.status)
      const { agent_text, audio_base64, is_complete } = res.data

      // Add agent turn to UI
      setDisplayedTurns((prev) => [...prev, { speaker: 'agent', text: agent_text, audio: audio_base64 }])

      // Play Sarvam TTS voice
      if (audio_base64) {
        await playAudio(audio_base64)
      } else {
        setAgentStatus('listening')
      }

      if (is_complete) {
        setCallState('ended')
        setAgentStatus('idle')
      } else {
        // Auto-listen after agent finishes speaking
        setTimeout(() => doStartListening(), 300)
      }
    } catch (err) {
      console.error('Turn error:', err)
      const detail = err.response?.data?.detail || err.message || 'Unknown error'
      setError(`Error: ${detail}`)
      setAgentStatus('listening')
    } finally {
      setIsSending(false)
    }
  }, [doStopListening, doStartListening, playAudio])

  // Listen for speech results via custom event (avoids stale closure)
  useEffect(() => {
    const handler = (e) => {
      handleCitizenMessage(e.detail)
    }
    window.addEventListener('jansamvaad-speech', handler)
    return () => window.removeEventListener('jansamvaad-speech', handler)
  }, [handleCitizenMessage])

  // Initiate new call
  const handleStartCall = useCallback(async () => {
    setCallState('connecting')
    setError('')
    setSummaryData(null)
    setDisplayedTurns([])

    const payload = {
      citizen_name: form.citizen_name?.trim() || 'नागरिक',
      survey_topic: form.survey_topic,
      phone_number: callMode === 'phone' ? form.phone_number?.trim() : '',
    }

    try {
      console.log('Initiating call...')
      const res = await initiateCall(payload)
      console.log('Call initiated:', res.data.call_id)
      setActiveCall(res.data)
      activeCallRef.current = res.data  // Set ref immediately
      setCallState('active')

      // Initial greeting from backend
      if (res.data.greeting_text) {
        setDisplayedTurns([{ speaker: 'agent', text: res.data.greeting_text, audio: res.data.audio_base64 }])
      }

      // Play initial audio greeting
      if (res.data.audio_base64) {
        await playAudio(res.data.audio_base64)
      } else {
        setAgentStatus('listening')
      }

      // Start listening after greeting finishes
      setTimeout(() => doStartListening(), 300)
    } catch (err) {
      console.error('Initiate error:', err)
      setError(`Could not initiate call: ${err.response?.data?.detail || err.message}`)
      setCallState('idle')
    }
  }, [form, callMode, playAudio, doStartListening])

  // End Call
  const handleEndCall = useCallback(async () => {
    doStopListening()
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    if (activeCallRef.current) {
      try {
        const res = await endCall(activeCallRef.current.call_id)
        if (res.data?.summary) {
          setSummaryData(res.data.summary)
        }
      } catch (_) {}
    }
    setCallState('ended')
    setAgentStatus('idle')
  }, [doStopListening])

  // Submit text input
  const handleTextSubmit = (e) => {
    e.preventDefault()
    if (textInput.trim() && !isSending) {
      handleCitizenMessage(textInput.trim())
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          JanSamvaad AI Live Voice Call
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-saffron/20 text-saffron border border-saffron/30 font-medium">
            Hindi • Sarvam AI • Gemini
          </span>
        </h1>
        <p className="text-slate-400 text-sm font-hindi mt-1">
          नागरिकों के साथ लाइव हिंदी आवाज़ में बातचीत एवं सर्वे
        </p>
      </div>

      {/* SETUP FORM */}
      {callState === 'idle' && (
        <div className="card space-y-5">
          {/* Mode Switcher Tabs */}
          <div>
            <label className="text-slate-400 text-xs uppercase tracking-wider mb-2 block font-semibold">Choose Call Mode</label>
            <div className="grid grid-cols-2 gap-3 p-1 bg-slate-900/60 rounded-xl border border-slate-700/80">
              <button
                type="button"
                onClick={() => setCallMode('web')}
                className={`flex items-center justify-center gap-2 py-3 px-3 rounded-lg text-sm font-semibold transition-all ${
                  callMode === 'web'
                    ? 'bg-saffron text-slate-950 shadow-md scale-[1.01]'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Globe className="w-4 h-4" />
                <span>🌐 Online Web Call</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${
                  callMode === 'web' ? 'bg-slate-950/20 text-slate-950' : 'bg-emerald-500/20 text-emerald-400'
                }`}>Free</span>
              </button>

              <button
                type="button"
                onClick={() => setCallMode('phone')}
                className={`flex items-center justify-center gap-2 py-3 px-3 rounded-lg text-sm font-semibold transition-all ${
                  callMode === 'phone'
                    ? 'bg-emerald-600 text-white shadow-md scale-[1.01]'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Phone className="w-4 h-4" />
                <span>📱 Mobile Phone Call</span>
                <span className="text-[10px] bg-black/30 px-1.5 py-0.5 rounded font-mono">Exotel</span>
              </button>
            </div>
          </div>

          {/* Mode Banner */}
          {callMode === 'web' ? (
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-200/90 leading-relaxed flex items-center gap-2">
              <Globe className="w-4 h-4 text-saffron shrink-0" />
              <span>
                <strong>ऑनलाइन वेब कॉल:</strong> सीधे अपने लैपटॉप/मोबाइल के माइक और स्पीकर से हिंदी में बात करें। किसी सिम या टेलीकॉम की ज़रूरत नहीं।
              </span>
            </div>
          ) : (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-200/90 leading-relaxed flex items-center gap-2">
              <Phone className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                <strong>मोबाइल सेलुलर कॉल:</strong> Exotel के माध्यम से आपके भारतीय मोबाइल नंबर पर रियल फ़ोन कॉल जाएगी।
              </span>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="text-slate-400 text-xs uppercase tracking-wide mb-1 block">Citizen Name (नागरिक का नाम)</label>
              <input
                value={form.citizen_name}
                onChange={(e) => setForm((f) => ({ ...f, citizen_name: e.target.value }))}
                placeholder="उदा. रमेश कुमार"
                className="w-full px-3 py-2.5 bg-slate-700/80 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-saffron"
              />
            </div>

            {callMode === 'phone' && (
              <div>
                <label className="text-slate-400 text-xs uppercase tracking-wide mb-1 block">
                  Mobile Number (मोबाइल नंबर — 10 अंक)
                </label>
                <input
                  value={form.phone_number}
                  onChange={(e) => setForm((f) => ({ ...f, phone_number: e.target.value }))}
                  placeholder="+91 9991317827"
                  className="w-full px-3 py-2.5 bg-slate-700/80 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}

            <div>
              <label className="text-slate-400 text-xs uppercase tracking-wide mb-1 block">Survey Topic (सर्वे का विषय)</label>
              <select
                value={form.survey_topic}
                onChange={(e) => setForm((f) => ({ ...f, survey_topic: e.target.value }))}
                className="w-full px-3 py-2.5 bg-slate-700/80 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-saffron"
              >
                {SURVEY_TOPICS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            onClick={handleStartCall}
            className={`w-full justify-center py-3.5 text-base font-semibold rounded-lg flex items-center gap-2 shadow-lg transition-all cursor-pointer ${
              callMode === 'web'
                ? 'bg-saffron text-slate-950 hover:bg-saffron/90'
                : 'bg-emerald-600 text-white hover:bg-emerald-500'
            }`}
          >
            {callMode === 'web' ? (
              <>
                <Globe className="w-5 h-5" />
                Start Online Web Call (ऑनलाइन कॉल शुरू करें)
              </>
            ) : (
              <>
                <Phone className="w-5 h-5" />
                Dial Mobile Number (फोन पर कॉल मिलाएं)
              </>
            )}
          </button>
        </div>
      )}

      {/* CONNECTING STATE */}
      {callState === 'connecting' && (
        <div className="card flex flex-col items-center py-12 gap-4">
          <Loader2 className="w-10 h-10 text-saffron animate-spin" />
          <p className="text-white font-semibold">Connecting to JanSamvaad AI...</p>
          <p className="text-slate-400 text-sm">Synthesizing Hindi greeting via Sarvam AI & Gemini</p>
        </div>
      )}

      {/* ACTIVE CALL OR ENDED */}
      {(callState === 'active' || callState === 'ended') && (
        <div className="space-y-4">
          {/* Phone dial banner */}
          {activeCall?.phone_dialed && (
            <div className="card bg-emerald-950/40 border border-emerald-500/50 p-4 flex items-center gap-3">
              <Phone className="w-5 h-5 text-emerald-400 animate-bounce" />
              <div>
                <p className="text-white text-sm font-semibold">📞 Calling your mobile phone ({form.phone_number}) now!</p>
                <p className="text-emerald-300/80 text-xs">Please answer your phone to hear JanSamvaad AI.</p>
              </div>
            </div>
          )}

          {/* Status header */}
          <div className="card flex items-center justify-between border-slate-700">
            <div className="flex items-center gap-3">
              <div
                className={`w-3.5 h-3.5 rounded-full ${
                  callState === 'active'
                    ? agentStatus === 'speaking'
                      ? 'bg-saffron animate-ping'
                      : agentStatus === 'thinking'
                      ? 'bg-amber-500 animate-pulse'
                      : 'bg-emerald-400 animate-pulse'
                    : 'bg-slate-500'
                }`}
              />
              <div>
                <p className="text-white font-semibold text-sm">
                  {callState === 'active'
                    ? agentStatus === 'speaking'
                      ? '🎙️ AI Agent is Speaking...'
                      : agentStatus === 'thinking'
                      ? '🧠 Gemini is Thinking...'
                      : '👂 Listening to Citizen...'
                    : 'Call Completed'}
                </p>
                {activeCall && (
                  <p className="text-slate-400 text-xs">
                    {form.citizen_name || 'Citizen'} • Topic: {form.survey_topic}
                  </p>
                )}
              </div>
            </div>

            {callState === 'active' && (
              <button
                onClick={handleEndCall}
                className="p-2.5 rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors flex items-center gap-1 text-xs font-medium cursor-pointer"
                title="End Call"
              >
                <PhoneOff className="w-4 h-4" />
                End
              </button>
            )}
          </div>

          {/* Conversation Transcript */}
          <div className="card space-y-4">
            <h2 className="text-white font-semibold flex items-center gap-2">
              💬 Live Conversation
            </h2>
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
              {displayedTurns.map((turn, i) => (
                <div key={i} className={`flex ${turn.speaker === 'agent' ? 'justify-start' : 'justify-end'}`}>
                  <div
                    className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed font-hindi ${
                      turn.speaker === 'agent'
                        ? 'bg-saffron/10 text-saffron border border-saffron/20 rounded-tl-sm'
                        : 'bg-slate-700/80 text-white border border-slate-600 rounded-tr-sm'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-semibold uppercase tracking-wider opacity-60">
                        {turn.speaker === 'agent' ? 'AI Agent' : 'Citizen'}
                      </span>
                      {turn.audio && (
                        <button
                          type="button"
                          onClick={() => playAudio(turn.audio)}
                          className="hover:text-saffron text-slate-400 p-0.5 rounded transition-colors cursor-pointer"
                          title="Replay Voice"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                    {turn.text}
                  </div>
                </div>
              ))}
              <div ref={turnsEndRef} />
            </div>

            {/* Big Mic Button */}
            {callState === 'active' && (
              <div className="flex flex-col items-center justify-center p-3 bg-slate-800/60 rounded-xl border border-slate-700/80 my-2">
                <button
                  type="button"
                  disabled={isSending}
                  onClick={() => {
                    if (isListening) {
                      doStopListening()
                    } else {
                      setError('')
                      doStartListening()
                    }
                  }}
                  className={`p-4 rounded-full transition-all shadow-lg flex items-center justify-center cursor-pointer ${
                    isSending
                      ? 'bg-amber-600 text-white animate-pulse'
                      : isListening
                      ? 'bg-emerald-500 text-white animate-pulse ring-4 ring-emerald-500/30'
                      : 'bg-saffron text-slate-950 hover:bg-saffron/90'
                  }`}
                  title={isSending ? 'Processing...' : isListening ? 'Stop Listening' : 'Click to Speak'}
                >
                  <Mic className="w-7 h-7" />
                </button>
                <span className="text-xs text-slate-200 mt-2 font-medium">
                  {isSending
                    ? '🧠 Gemini सोच रहा है...'
                    : isListening
                    ? '🔴 माइक चालू है — बोलिए...'
                    : '🎙️ बोलने के लिए माइक बटन दबाएं'}
                </span>
                {error && <p className="text-xs text-amber-400 mt-1">{error}</p>}
              </div>
            )}

            {/* Text Input Bar */}
            {callState === 'active' && (
              <form onSubmit={handleTextSubmit} className="flex gap-2 pt-2 border-t border-slate-700/60">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="हिंदी या Hinglish में टाइप भी कर सकते हैं..."
                  className="flex-1 px-4 py-2.5 bg-slate-700/80 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-400 focus:outline-none focus:border-saffron"
                  disabled={isSending}
                />
                <button
                  type="submit"
                  disabled={!textInput.trim() || isSending}
                  className="btn-primary px-4 py-2.5 rounded-lg flex items-center justify-center disabled:opacity-50 cursor-pointer"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            )}
          </div>

          {/* Call Summary Card on End */}
          {callState === 'ended' && (
            <div className="card space-y-4 border-emerald-500/40 bg-emerald-950/20">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <CheckCircle2 className="w-5 h-5" />
                <span>Call Saved to MongoDB Atlas!</span>
              </div>
              {summaryData && (
                <p className="text-slate-300 text-sm font-hindi leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-slate-700">
                  {summaryData}
                </p>
              )}
              <button
                onClick={() => {
                  setCallState('idle')
                  setActiveCall(null)
                  setDisplayedTurns([])
                  setError('')
                }}
                className="btn-secondary w-full justify-center"
              >
                Start Another Call
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
