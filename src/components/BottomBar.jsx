export default function BottomBar({ hermesVersion, hermesPort, voiceState, memUsed, memTotal, gpuMem }) {
  return (
    <footer style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 20px', borderTop: '1px solid var(--border)',
      background: 'rgba(3,8,16,0.95)', height: '36px', flexShrink: 0,
      fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)',
      letterSpacing: '0.1em',
    }}>
      <div style={{ display: 'flex', gap: '20px' }}>
        {[
          { label: 'HERMES', val: hermesVersion, color: 'var(--green)' },
          { label: 'API', val: `localhost:${hermesPort}`, color: 'var(--green)' },
          { label: 'VOICE', val: voiceState, color: voiceState === 'ACTIVE' ? 'var(--green)' : 'var(--amber)' },
          { label: 'MEM', val: `${memUsed} / ${memTotal}`, color: 'var(--cyan)' },
          { label: 'GPU', val: `RTX 4070 · ${gpuMem}`, color: 'var(--cyan)' },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            {item.label} <span style={{ color: item.color }}>{item.val}</span>
          </div>
        ))}
      </div>
      <span>FRIDAY · NOUS RESEARCH HERMES BRIDGE · MIT</span>
    </footer>
  )
}
