import { useEffect, useState } from 'react'

export default function TopBar({ hermesOnline, onSettings }) {
  const [time, setTime] = useState('')

  useEffect(() => {
    const tick = () => {
      const now = new Date()
      const h = String(now.getHours()).padStart(2, '0')
      const m = String(now.getMinutes()).padStart(2, '0')
      const s = String(now.getSeconds()).padStart(2, '0')
      setTime(`${h}:${m}:${s}`)
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 20px', borderBottom: '1px solid var(--border)',
      background: 'rgba(3,8,16,0.95)', backdropFilter: 'blur(10px)',
      height: '48px', flexShrink: 0, zIndex: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <span style={{
          fontFamily: 'var(--display)', fontSize: '15px', fontWeight: 700,
          letterSpacing: '0.25em', color: 'var(--cyan)',
          textShadow: '0 0 18px rgba(0,200,255,0.5)',
        }}>F.R.I.D.A.Y</span>
        <div style={{ width: '1px', height: '20px', background: 'var(--border-bright)' }} />
        <span style={{
          fontFamily: 'var(--mono)', fontSize: '10px',
          color: 'var(--text-dim)', letterSpacing: '0.1em',
        }}>FULLY RESPONSIVE INTELLIGENCE DIGITAL ASSISTANT YEAH</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--text-dim)', letterSpacing: '0.1em' }}>
          <div style={{
            width: '7px', height: '7px', borderRadius: '50%',
            background: hermesOnline ? 'var(--green)' : 'var(--red)',
            boxShadow: hermesOnline ? '0 0 8px var(--green)' : '0 0 8px var(--red)',
            animation: 'pulse-dot 2s infinite',
          }} />
          HERMES {hermesOnline ? 'ONLINE' : 'OFFLINE'}
        </div>
        <div style={{ width: '1px', height: '20px', background: 'var(--border)' }} />
        <span style={{ fontFamily: 'var(--mono)', fontSize: '11px', color: 'var(--cyan-dim)', letterSpacing: '0.1em' }}>{time}</span>
        <button onClick={onSettings} style={{
          background: 'none', border: '1px solid var(--border)',
          color: 'var(--text-dim)', fontFamily: 'var(--mono)',
          fontSize: '10px', padding: '4px 10px', borderRadius: '3px',
          cursor: 'pointer', letterSpacing: '0.1em',
        }}>SETTINGS</button>
      </div>
    </header>
  )
}