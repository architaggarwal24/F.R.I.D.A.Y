/**
 * useConversation — persists chat history in localStorage
 * Automatically saves on every message, restores on mount.
 * Caps at MAX_MESSAGES to avoid unbounded growth.
 */
import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY  = 'friday_conversation'
const MAX_MESSAGES = 200

const INITIAL_MESSAGE = {
  role: 'friday',
  content: "Good morning, boss. All systems nominal. Hermes is online. What's the mission?",
  time: new Date().toTimeString().slice(0, 8),
}

export default function useConversation() {
  const [messages, setMessages] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length > 0) return parsed
      }
    } catch {}
    return [INITIAL_MESSAGE]
  })

  // Persist to localStorage on every change
  useEffect(() => {
    try {
      // Keep only last MAX_MESSAGES
      const toStore = messages.slice(-MAX_MESSAGES)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore))
    } catch {}
  }, [messages])

  const addMessage = useCallback((msg) => {
    setMessages(prev => [...prev, msg].slice(-MAX_MESSAGES))
  }, [])

  const updateLastMessage = useCallback((updater) => {
    setMessages(prev => {
      const updated = [...prev]
      updated[updated.length - 1] = updater(updated[updated.length - 1])
      return updated
    })
  }, [])

  const clearHistory = useCallback(() => {
    try { localStorage.removeItem(STORAGE_KEY) } catch {}
    setMessages([INITIAL_MESSAGE])
  }, [])

  return { messages, setMessages, addMessage, updateLastMessage, clearHistory }
}
