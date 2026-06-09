import { useEffect, useRef, useCallback } from 'react'

const WS_URL         = import.meta.env.VITE_VOICE_WS_URL || 'ws://localhost:5175'
const RECONNECT_DELAY = 3000

export default function useVoice({ onState, onAudioLevel, onVoiceInput, enabled }) {
  const wsRef        = useRef(null)
  const reconnectRef = useRef(null)
  const mountedRef   = useRef(true)

  const connect = useCallback(() => {
    if (!enabled || !mountedRef.current) return
    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[Voice] WebSocket connected')
        onState?.('idle', true)
      }

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          switch (msg.type) {
            case 'state':       onState?.(msg.state, msg.wakeWordOn ?? true); break
            case 'audio_level': onAudioLevel?.(msg.level); break
            case 'voice_input': onVoiceInput?.(msg.text);  break
          }
        } catch {}
      }

      ws.onclose = () => {
        onState?.('idle', false)
        if (mountedRef.current)
          reconnectRef.current = setTimeout(connect, RECONNECT_DELAY)
      }

      ws.onerror = () => ws.close()
    } catch (e) {
      if (mountedRef.current)
        reconnectRef.current = setTimeout(connect, RECONNECT_DELAY)
    }
  }, [enabled, onState, onAudioLevel, onVoiceInput])

  useEffect(() => {
    mountedRef.current = true
    if (enabled) connect()
    return () => {
      mountedRef.current = false
      clearTimeout(reconnectRef.current)
      wsRef.current?.close()
    }
  }, [enabled, connect])

  const speak = useCallback((text) => {
    if (wsRef.current?.readyState === WebSocket.OPEN)
      wsRef.current.send(JSON.stringify({ type: 'tts', text }))
  }, [])

  return { speak }
}
