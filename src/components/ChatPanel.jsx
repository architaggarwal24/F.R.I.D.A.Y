import { useRef, useEffect } from 'react'

function Message({ role, content, time }) {
  const isFriday = role === 'friday'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', letterSpacing: '0.15em', textTransform: 'uppercase', color: isFriday ? 'var(--cyan)' : 'var(--amber)' }}>
          {isFriday ? 'FRIDAY' : 'YOU'}
        </span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)' }}>{time}</span>
      </div>
      <div style={{
        padding: '10px 12px', borderRadius: '3px', fontSize: '12.5px',
        lineHeight: '1.6', fontFamily: 'var(--body)', fontWeight: 300,
        ...(isFriday
          ? { background: 'rgba(0,80,160,0.15)', border: '1px solid rgba(0,180,255,0.12)', borderLeft: '2px solid rgba(0,200,255,0.4)', color: 'var(--text-bright)' }
          : { background: 'rgba(255,160,50,0.07)', border: '1px solid rgba(255,160,50,0.12)', borderLeft: '2px solid rgba(255,179,71,0.4)', color: 'var(--text)', alignSelf: 'flex-end', maxWidth: '90%' }
        ),
      }}>
        {content}
      </div>
    </div>
  )
}

function TypingIndicator({ subagents }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', background: 'rgba(0,80,160,0.1)', border: '1px solid rgba(0,180,255,0.1)', borderLeft: '2px solid rgba(0,200,255,0.3)', borderRadius: '3px', width: 'fit-content' }}>
      <div style={{ display: 'flex', gap: '4px' }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--cyan-dim)', animation: `typing-bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
        ))}
      </div>
      <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.1em' }}>
        PROCESSING{subagents > 0 ? ` · ${subagents} SUBAGENT${subagents > 1 ? 'S' : ''} ACTIVE` : ''}
      </span>
    </div>
  )
}

export default function ChatPanel({ messages, isThinking, subagents, input, setInput, onSend, onVoice, voiceActive, wakeWordOn, onClear }) {
  const endRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, isThinking])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend() }
  }

  const handleInput = (e) => {
    setInput(e.target.value)
    const ta = textareaRef.current
    if (ta) { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 100) + 'px' }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <span style={{ fontFamily: 'var(--display)', fontSize: '9px', fontWeight: 600, letterSpacing: '0.22em', color: 'var(--cyan)', textTransform: 'uppercase' }}>Command Interface</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button onClick={onClear} title="Clear conversation history" style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '3px', color: 'var(--text-dim)', fontFamily: 'var(--mono)', fontSize: '9px', padding: '2px 8px', cursor: 'pointer', letterSpacing: '0.1em' }}>CLEAR</button>
          <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.08em' }}>HERMES BRIDGE</span>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {messages.map((msg, i) => <Message key={i} {...msg} />)}
        {isThinking && <TypingIndicator subagents={subagents} />}
        <div ref={endRef} />
      </div>

      <div style={{ borderTop: '1px solid var(--border)', padding: '10px 12px', flexShrink: 0, background: 'rgba(3,8,16,0.8)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Give FRIDAY a mission..."
            rows={1}
            style={{
              flex: 1, background: 'rgba(0,20,50,0.6)', border: '1px solid var(--border)',
              borderRadius: '3px', color: 'var(--text)', fontFamily: 'var(--mono)',
              fontSize: '12px', padding: '8px 10px', resize: 'none', outline: 'none',
              lineHeight: '1.5', minHeight: '36px', transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = 'rgba(0,200,255,0.35)'}
            onBlur={e => e.target.style.borderColor = 'var(--border)'}
          />
          <button onClick={onVoice} style={{
            background: voiceActive ? 'rgba(255,60,80,0.25)' : 'rgba(255,60,80,0.1)',
            border: `1px solid ${voiceActive ? 'rgba(255,60,80,0.5)' : 'rgba(255,60,80,0.2)'}`,
            borderRadius: '3px', color: 'var(--red)', fontFamily: 'var(--mono)',
            fontSize: '10px', padding: '8px 10px', cursor: 'pointer',
            letterSpacing: '0.1em', height: '36px', whiteSpace: 'nowrap',
            animation: voiceActive ? 'voice-pulse 1s ease-in-out infinite' : 'none',
          }}>◉ {voiceActive ? 'LIVE' : 'MIC'}</button>
          <button onClick={onSend} style={{
            background: 'rgba(0,100,200,0.2)', border: '1px solid rgba(0,180,255,0.25)',
            borderRadius: '3px', color: 'var(--cyan)', fontFamily: 'var(--mono)',
            fontSize: '10px', padding: '8px 10px', cursor: 'pointer',
            letterSpacing: '0.1em', height: '36px', whiteSpace: 'nowrap',
          }}>SEND ›</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px' }}>
          <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.08em' }}>
            ENTER to send · SHIFT+ENTER newline · <span style={{ color: 'var(--cyan-dim)' }}>"Hey Friday"</span> for voice
          </span>
          <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: wakeWordOn ? 'var(--green-dim)' : 'var(--text-dim)', letterSpacing: '0.08em' }}>
            {wakeWordOn ? '● WAKE WORD ON' : '○ WAKE WORD OFF'}
          </span>
        </div>
      </div>
    </div>
  )
}