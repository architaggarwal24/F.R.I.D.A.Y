const TYPE_COLORS = {
  WEB:    'var(--cyan)',
  TOOL:   'var(--amber)',
  AGENT:  'var(--green)',
  SKILL:  '#c084fc',
  MEM:    '#fb923c',
}

function FeedItem({ type, label, detail, time, active }) {
  return (
    <div style={{
      padding: '8px 14px', borderBottom: '1px solid rgba(0,180,255,0.06)',
      cursor: 'pointer', transition: 'background 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,200,255,0.04)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', letterSpacing: '0.12em', color: TYPE_COLORS[type] || 'var(--text-dim)' }}>{type}</span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)' }}>{time}</span>
      </div>
      <div style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</div>
      {detail && <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{detail}</div>}
      {active && (
        <div style={{ height: '2px', borderRadius: '1px', marginTop: '5px', overflow: 'hidden', background: 'rgba(0,180,255,0.08)' }}>
          <div style={{ height: '100%', borderRadius: '1px', background: TYPE_COLORS[type], animation: 'bar-scan 2.5s ease-in-out infinite' }} />
        </div>
      )}
    </div>
  )
}

export default function ActivityFeed({ events }) {
  const active = events.filter(e => e.active)
  const recent = events.filter(e => !e.active)

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      borderRight: '1px solid var(--border)', background: 'var(--panel)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px', borderBottom: '1px solid var(--border)', flexShrink: 0,
      }}>
        <span style={{ fontFamily: 'var(--display)', fontSize: '9px', fontWeight: 600, letterSpacing: '0.22em', color: 'var(--cyan)', textTransform: 'uppercase' }}>Activity Feed</span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.08em' }}>LIVE</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '10px 0' }}>
        {active.length > 0 && (
          <>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.15em', textTransform: 'uppercase', padding: '6px 14px 4px' }}>Active</div>
            {active.map((e, i) => <FeedItem key={i} {...e} active />)}
          </>
        )}
        {recent.length > 0 && (
          <>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.15em', textTransform: 'uppercase', padding: '10px 14px 4px' }}>Recent</div>
            {recent.map((e, i) => <FeedItem key={i} {...e} />)}
          </>
        )}
        {events.length === 0 && (
          <div style={{ padding: '20px 14px', fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--text-dim)', textAlign: 'center' }}>NO ACTIVITY YET</div>
        )}
      </div>
    </div>
  )
}
