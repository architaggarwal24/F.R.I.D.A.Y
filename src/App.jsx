import { useState, useEffect, useCallback } from 'react'
import TopBar from './components/TopBar'
import ActivityFeed from './components/ActivityFeed'
import OrbPanel from './components/OrbPanel'
import ChatPanel from './components/ChatPanel'
import BottomBar from './components/BottomBar'
import SettingsDrawer from './components/SettingsDrawer'
import { sendMessage } from './api'
import useVoice from './useVoice'
import useConversation from './useConversation'

export default function App() {
  const { messages, addMessage, updateLastMessage, clearHistory } = useConversation()
  const [input, setInput]               = useState('')
  const [voiceActive, setVoiceActive]   = useState(false)
  const [wakeWordOn, setWakeWordOn]     = useState(false)
  const [orbState, setOrbState]         = useState('idle')
  const [isThinking, setIsThinking]     = useState(false)
  const [audioLevel, setAudioLevel]     = useState(0)
  const [events, setEvents]             = useState([])
  const [hermesOnline, setHermesOnline] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [hermesConfig, setHermesConfig] = useState({ model: '...', provider: '...' })
  const [hermesStats,  setHermesStats]  = useState({ skills: '...', tools: '...', sessions: 0 })
  const [subagents, setSubagents]       = useState(0)

  const fetchConfig = () => {
    fetch('http://localhost:5174/bridge/config')
      .then(r => r.json())
      .then(d => { if (d.model) setHermesConfig(d) })
      .catch(() => {})
  }

  const fetchStats = () => {
    fetch('http://localhost:5174/bridge/stats')
      .then(r => r.json())
      .then(d => setHermesStats({ skills: d.skills, tools: d.tools, sessions: d.sessions }))
      .catch(() => {})
  }

  // Health check + config + stats on mount
  useEffect(() => {
    fetch('http://localhost:8642/v1/health')
      .then(r => r.json())
      .then(d => setHermesOnline(d.status === 'ok'))
      .catch(() => setHermesOnline(false))
    fetchConfig()
    fetchStats()
  }, [])

  const now = () => new Date().toTimeString().slice(0, 8)

  const addEvent = (type, label, detail) =>
    setEvents(prev => [{ type, label, detail, time: now(), active: false }, ...prev].slice(0, 50))

  // ── Chat send (used by both text and voice) ──────────────
  const handleSend = useCallback(async (textOverride) => {
    const text = (textOverride ?? input).trim()
    if (!text || isThinking) return

    const userMsg      = { role: 'user', content: text, time: now() }
    const nextMessages = [...messages, userMsg]
    addMessage(userMsg)
    setInput('')
    setIsThinking(true)
    setOrbState('thinking')
    addEvent('WEB', 'chat_request', text.slice(0, 40))

    const replyTime = now()
    let accumulated = ''
    let replyAdded  = false

    const onToken = (token) => {
      accumulated += token
      if (!replyAdded) {
        replyAdded = true
        addMessage({ role: 'friday', content: accumulated, time: replyTime })
      } else {
        updateLastMessage(() => ({ role: 'friday', content: accumulated, time: replyTime }))
      }
    }

    const onTool = ({ type, label, detail, active }) => {
      setEvents(prev => {
        // If active=true and same label exists as active, update it; else prepend
        if (!active) {
          return prev.map(e =>
            e.label === label && e.active
              ? { ...e, active: false }
              : e
          )
        }
        return [{ type, label, detail, time: now(), active: true }, ...prev].slice(0, 50)
      })
      // Bump subagent count when a delegate/agent tool fires
      if (type === 'AGENT') setSubagents(n => n + 1)
    }

    const onDone = () => {
      setIsThinking(false)
      setSubagents(0)
      setOrbState('idle')
      addEvent('AGENT', 'response_complete', `${accumulated.length} chars`)
      if (accumulated) speak(accumulated)
    }

    const onError = (err) => {
      setIsThinking(false)
      setSubagents(0)
      setOrbState('error')
      setMessages(prev => [...prev, { role: 'friday', content: `⚠ ${err}`, time: now() }])
      addEvent('TOOL', 'hermes_error', err.slice(0, 40))
      setTimeout(() => setOrbState('idle'), 3000)
    }

    await sendMessage(nextMessages, onToken, onTool, onDone, onError)
  }, [input, messages, isThinking])

  // ── Voice pipeline hooks ─────────────────────────────────
  const handleVoiceState = useCallback((state, wakeOn) => {
    setOrbState(state)
    setWakeWordOn(wakeOn ?? false)
    if (state === 'listening') setVoiceActive(true)
    if (state === 'idle')      setVoiceActive(false)
  }, [])

  const handleAudioLevel = useCallback((level) => {
    setAudioLevel(level)
  }, [])

  const handleVoiceInput = useCallback((text) => {
    addEvent('MEM', 'voice_input', text.slice(0, 40))
    handleSend(text)
  }, [handleSend])

  const { speak } = useVoice({
    enabled: true,   // always try to connect; silently reconnects if pipeline not running
    onState:      handleVoiceState,
    onAudioLevel: handleAudioLevel,
    onVoiceInput: handleVoiceInput,
  })

  const handleMicClick = () => {
    if (voiceActive) return  // already recording
    fetch('http://localhost:5176/trigger', { method: 'POST' })
      .catch(() => console.warn('[MIC] Voice pipeline not running'))
  }

  return (
    <div style={{ display: 'grid', gridTemplateRows: '48px 1fr 36px', height: '100vh', width: '100%', overflow: 'hidden', position: 'relative' }}>
      {/* Scanline */}
      <div style={{ pointerEvents: 'none', position: 'fixed', inset: 0, zIndex: 100, background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px)' }} />
      <div style={{ pointerEvents: 'none', position: 'fixed', top: '-2%', left: 0, right: 0, height: '8px', background: 'linear-gradient(transparent, rgba(0,200,255,0.04), transparent)', zIndex: 101, animation: 'scan-sweep 8s linear infinite' }} />

      <TopBar hermesOnline={hermesOnline} onSettings={() => setSettingsOpen(true)} />

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 360px', overflow: 'hidden' }}>
        <ActivityFeed events={events} />
        <OrbPanel
          orbState={orbState}
          audioLevel={audioLevel}
          stats={{
            model:     hermesConfig.model,
            memory:    `${hermesStats.skills} skills`,
            tools:     `${hermesStats.tools} active`,
            subagents: `${subagents} running`,
            skills:    ['web-research','code-runner','file-ops','pdf-parse','arxiv','github','memory','+more'],
          }}
          provider={{
            abbr:  hermesConfig.provider?.slice(0, 2).toUpperCase() || 'NV',
            name:  hermesConfig.provider || 'nvidia',
            model: hermesConfig.model,
          }}
        />
        <ChatPanel
          messages={messages}
          isThinking={isThinking}
          subagents={subagents}
          input={input}
          setInput={setInput}
          onSend={() => handleSend()}
          onVoice={handleMicClick}
          voiceActive={voiceActive}
          wakeWordOn={wakeWordOn}
          onClear={clearHistory}
        />
      </div>

      <BottomBar
        hermesVersion="v0.14.0"
        hermesPort="8642"
        voiceState={wakeWordOn ? 'ACTIVE' : 'READY'}
        memUsed="8.2 GB"
        memTotal="32 GB"
        gpuMem="4.1 GB"
      />

      <SettingsDrawer open={settingsOpen} onClose={() => { setSettingsOpen(false); fetchConfig(); fetchStats() }} />
    </div>
  )
}