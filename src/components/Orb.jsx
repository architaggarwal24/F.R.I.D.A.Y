import { useEffect, useRef, useState } from 'react'

const STATE_CONFIG = {
  idle:      { color: '#00c8ff', glow: 'rgba(0,200,255,0.35)',   ring: 'rgba(0,200,255,0.15)', speed: 6  },
  listening: { color: '#ffe040', glow: 'rgba(255,224,64,0.5)',   ring: 'rgba(255,224,64,0.2)', speed: 2  },
  thinking:  { color: '#a855f7', glow: 'rgba(168,85,247,0.45)',  ring: 'rgba(168,85,247,0.2)', speed: 3  },
  speaking:  { color: '#00ff9d', glow: 'rgba(0,255,157,0.5)',    ring: 'rgba(0,255,157,0.2)',  speed: 1.5},
  error:     { color: '#ff4060', glow: 'rgba(255,64,96,0.5)',    ring: 'rgba(255,64,96,0.2)',  speed: 4  },
}

export default function Orb({ state = 'idle', audioLevel = 0 }) {
  const cfg      = STATE_CONFIG[state] || STATE_CONFIG.idle
  const [tick, setTick] = useState(0)
  const prevCfg  = useRef(cfg)
  const animRef  = useRef(null)
  const startRef = useRef(Date.now())

  // Animate tick for ring rotation
  useEffect(() => {
    let raf
    const loop = () => {
      setTick(Date.now())
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [])

  const elapsed  = (Date.now() - startRef.current) / 1000
  const pulse    = 0.5 + 0.5 * Math.sin(elapsed * 2.5)
  const audioBump = audioLevel * 30
  const coreSize = 110 + pulse * 8 + audioBump
  const glowSize = coreSize * 1.8 + audioBump * 2

  const ring = (size, durationS, reverse = false, dashed = false) => {
    const angle = ((elapsed * (360 / durationS)) % 360) * (reverse ? -1 : 1)
    return (
      <div style={{
        position: 'absolute',
        width: size, height: size,
        borderRadius: '50%',
        border: `1px ${dashed ? 'dashed' : 'solid'} ${cfg.ring}`,
        transform: `rotate(${angle}deg)`,
        transition: 'border-color 1s ease',
        left: '50%', top: '50%',
        marginLeft: -size/2, marginTop: -size/2,
      }} />
    )
  }

  return (
    <div style={{ position: 'relative', width: 280, height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

      {/* Outer glow */}
      <div style={{
        position: 'absolute',
        width: glowSize * 1.4, height: glowSize * 1.4,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${cfg.glow} 0%, transparent 70%)`,
        filter: 'blur(18px)',
        transition: 'background 1s ease',
        pointerEvents: 'none',
      }} />

      {/* Rings */}
      {ring(220, 18, false, false)}
      {ring(186, 12, true,  true )}
      {ring(152, 7,  false, false)}

      {/* Core sphere */}
      <div style={{
        position: 'absolute',
        width: coreSize, height: coreSize,
        borderRadius: '50%',
        background: `
          radial-gradient(circle at 35% 32%,
            rgba(255,255,255,0.18) 0%,
            ${cfg.color}55 25%,
            ${cfg.color}22 60%,
            rgba(0,0,0,0.5) 100%
          )
        `,
        border: `1px solid ${cfg.color}66`,
        boxShadow: `
          0 0 ${20 + pulse * 15}px ${cfg.glow},
          0 0 ${40 + pulse * 20}px ${cfg.glow.replace('0.', '0.0')},
          inset 0 0 20px rgba(0,0,0,0.6)
        `,
        transition: 'background 1s ease, border-color 1s ease',
      }}>
        {/* Inner highlight */}
        <div style={{
          position: 'absolute',
          top: '18%', left: '22%',
          width: '35%', height: '28%',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,255,255,0.25) 0%, transparent 100%)',
          transform: 'rotate(-30deg)',
        }} />
      </div>

      {/* Equator line */}
      <div style={{
        position: 'absolute',
        width: coreSize * 1.05,
        height: 1,
        background: `linear-gradient(90deg, transparent 0%, ${cfg.color}44 30%, ${cfg.color}66 50%, ${cfg.color}44 70%, transparent 100%)`,
        transition: 'background 1s ease',
        pointerEvents: 'none',
      }} />
    </div>
  )
}