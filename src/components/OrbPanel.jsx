import Orb from './Orb'

const STATE_LABELS = {
  idle:      { text: 'IDLE',      color: '#00c8ff' },
  listening: { text: 'LISTENING', color: '#ffe040' },
  thinking:  { text: 'THINKING',  color: '#a855f7' },
  speaking:  { text: 'SPEAKING',  color: '#00ff9d' },
  error:     { text: 'ERROR',     color: '#ff4060' },
}

export default function OrbPanel({ orbState = 'idle', audioLevel = 0, stats, provider }) {
  const label = STATE_LABELS[orbState] || STATE_LABELS.idle

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      borderRight: '1px solid var(--border)', background: 'var(--panel)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px', borderBottom: '1px solid var(--border)',
        flexShrink: 0, width: '100%',
      }}>
        <span style={{ fontFamily: 'var(--display)', fontSize: '9px', fontWeight: 600, letterSpacing: '0.22em', color: 'var(--cyan)', textTransform: 'uppercase' }}>Core Status</span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.08em' }}>SYSTEM</span>
      </div>

      {/* Orb */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        <div style={{ position: 'relative', width: '280px', height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {/* Glow behind orb - z-index 0 */}
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            background: `radial-gradient(circle, ${label.color}22 0%, transparent 70%)`,
            filter: 'blur(24px)', transition: 'background 1s ease',
            zIndex: 0, pointerEvents: 'none',
          }} />
          {/* Canvas on top - z-index 1 */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            <Orb state={orbState} audioLevel={audioLevel} />
          </div>
        </div>

        {/* State label */}
        <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '6px', height: '6px', borderRadius: '50%',
            background: label.color,
            boxShadow: `0 0 8px ${label.color}`,
            animation: 'pulse-dot 2s infinite',
          }} />
          <span style={{
            fontFamily: 'var(--mono)', fontSize: '11px',
            letterSpacing: '0.3em', color: label.color,
            textTransform: 'uppercase',
            textShadow: `0 0 12px ${label.color}80`,
          }}>
            {label.text}
            {orbState === 'idle' && <span style={{ animation: 'blink 1s step-end infinite' }}>_</span>}
          </span>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ width: '100%', padding: '0 16px 12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', flexShrink: 0 }}>
        {[
          { label: 'MODEL',     val: stats.model,     color: 'var(--cyan)'  },
          { label: 'MEMORY',    val: stats.memory,    color: 'var(--green)' },
          { label: 'TOOLS',     val: stats.tools,     color: 'var(--cyan)'  },
          { label: 'SUBAGENTS', val: stats.subagents, color: 'var(--amber)' },
        ].map(s => (
          <div key={s.label} style={{ background: 'rgba(0,20,50,0.6)', border: '1px solid var(--border)', borderRadius: '4px', padding: '8px 10px' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.12em', marginBottom: '3px' }}>{s.label}</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: s.label === 'MODEL' ? '10px' : '13px', color: s.color }}>{s.val}</div>
          </div>
        ))}
      </div>

      {/* Provider */}
      <div style={{ width: 'calc(100% - 32px)', margin: '0 16px 12px', border: '1px solid var(--border)', borderRadius: '4px', padding: '8px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,20,50,0.4)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '3px', background: 'linear-gradient(135deg,rgba(0,150,255,0.3),rgba(0,80,180,0.3))', border: '1px solid rgba(0,180,255,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--cyan)' }}>
            {provider.abbr}
          </div>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--text)', letterSpacing: '0.08em' }}>{provider.name}</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.06em', maxWidth: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{provider.model}</div>
          </div>
        </div>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--green)', border: '1px solid var(--green-dim)', padding: '2px 6px', borderRadius: '2px', letterSpacing: '0.1em' }}>LIVE</div>
      </div>

      {/* Skills */}
      <div style={{ width: 'calc(100% - 32px)', margin: '0 16px 16px', flexShrink: 0 }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '6px' }}>Loaded Skills</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
          {stats.skills.map(s => (
            <span key={s} style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'rgba(180,130,255,0.8)', border: '1px solid rgba(180,130,255,0.2)', padding: '2px 7px', borderRadius: '2px', letterSpacing: '0.06em' }}>{s}</span>
          ))}
        </div>
      </div>
    </div>
  )
}