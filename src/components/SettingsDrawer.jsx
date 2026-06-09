import { useState, useEffect } from 'react'

const BRIDGE = 'http://localhost:5174'

const PROVIDERS = [
  { id: 'nvidia',     label: 'NVIDIA NIM',   abbr: 'NV', secretKey: 'NVIDIA_API_KEY',      baseUrl: 'https://integrate.api.nvidia.com/v1' },
  { id: 'openrouter', label: 'OpenRouter',   abbr: 'OR', secretKey: 'OPENROUTER_API_KEY',   baseUrl: null },
  { id: 'anthropic',  label: 'Anthropic',    abbr: 'AN', secretKey: 'ANTHROPIC_API_KEY',    baseUrl: null },
  { id: 'groq',       label: 'Groq (LLM)',   abbr: 'GQ', secretKey: 'GROQ_API_KEY',         baseUrl: null },
  { id: 'google',     label: 'Google Gemini',abbr: 'GG', secretKey: 'GOOGLE_API_KEY',       baseUrl: null },
  { id: 'ollama',     label: 'Ollama (Local)',abbr: 'OL', secretKey: 'OLLAMA_BASE_URL',      baseUrl: null },
]

const NVIDIA_MODELS = [
  'meta/llama-3.3-70b-instruct',
  'deepseek-ai/deepseek-v4-flash',
  'mistralai/mistral-large-2-instruct',
  'nvidia/llama-3.1-nemotron-70b-instruct',
  'google/gemma-3-27b-it',
]

function Field({ label, children, hint }) {
  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '5px' }}>{label}</div>
      {children}
      {hint && <div style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'rgba(160,210,240,0.3)', marginTop: '3px' }}>{hint}</div>}
    </div>
  )
}

function Input({ value, onChange, placeholder, type = 'text', mono = true }) {
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: '100%', background: 'rgba(0,20,50,0.7)',
        border: '1px solid var(--border)', borderRadius: '3px',
        color: 'var(--text)', fontFamily: mono ? 'var(--mono)' : 'var(--body)',
        fontSize: '11px', padding: '7px 10px', outline: 'none',
        transition: 'border-color 0.2s', boxSizing: 'border-box',
      }}
      onFocus={e => e.target.style.borderColor = 'rgba(0,200,255,0.4)'}
      onBlur={e => e.target.style.borderColor = 'var(--border)'}
    />
  )
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        width: '100%', background: 'rgba(0,20,50,0.7)',
        border: '1px solid var(--border)', borderRadius: '3px',
        color: 'var(--text)', fontFamily: 'var(--mono)',
        fontSize: '11px', padding: '7px 10px', outline: 'none',
        cursor: 'pointer', boxSizing: 'border-box',
      }}
    >
      {options.map(o => <option key={o.value} value={o.value} style={{ background: '#060d1a' }}>{o.label}</option>)}
    </select>
  )
}

function SaveBtn({ onClick, saving, saved }) {
  return (
    <button onClick={onClick} style={{
      background: saved ? 'rgba(0,255,157,0.15)' : 'rgba(0,100,200,0.2)',
      border: `1px solid ${saved ? 'var(--green-dim)' : 'rgba(0,180,255,0.25)'}`,
      borderRadius: '3px', color: saved ? 'var(--green)' : 'var(--cyan)',
      fontFamily: 'var(--mono)', fontSize: '10px', padding: '8px 16px',
      cursor: 'pointer', letterSpacing: '0.1em', transition: 'all 0.2s',
      opacity: saving ? 0.6 : 1,
    }}>
      {saving ? 'SAVING...' : saved ? '✓ SAVED' : 'APPLY'}
    </button>
  )
}

function SectionHeader({ label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '20px 0 12px' }}>
      <span style={{ fontFamily: 'var(--display)', fontSize: '8px', fontWeight: 600, letterSpacing: '0.25em', color: 'var(--cyan)', textTransform: 'uppercase' }}>{label}</span>
      <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
    </div>
  )
}

export default function SettingsDrawer({ open, onClose }) {
  const [provider,    setProvider]    = useState('nvidia')
  const [apiKey,      setApiKey]      = useState('')
  const [model,       setModel]       = useState('meta/llama-3.3-70b-instruct')
  const [customModel, setCustomModel] = useState('')
  const [useCustom,   setUseCustom]   = useState(false)
  const [groqKey,     setGroqKey]     = useState('')
  const [elevenKey,   setElevenKey]   = useState('')
  const [elevenVoice, setElevenVoice] = useState('')
  const [saving,      setSaving]      = useState(false)
  const [saved,       setSaved]       = useState(false)
  const [error,       setError]       = useState('')

  const post = async (path, body) => {
    const r = await fetch(`${BRIDGE}${path}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.error || 'Bridge error')
    return d
  }

  const handleSave = async () => {
    setSaving(true); setError('')
    try {
      const prov = PROVIDERS.find(p => p.id === provider)
      const finalModel = useCustom ? customModel : model

      // Set provider + model
      await post('/bridge/config', { key: 'model.provider', value: provider })
      await post('/bridge/config', { key: 'model.default',  value: finalModel })
      await post('/bridge/config', { key: 'auxiliary.provider', value: provider })

      // Set API key if provided
      if (apiKey && prov?.secretKey) {
        await post('/bridge/secret', { key: prov.secretKey, value: apiKey })
      }

      // Voice keys
      if (groqKey)     await post('/bridge/secret', { key: 'GROQ_API_KEY',       value: groqKey })
      if (elevenKey)   await post('/bridge/secret', { key: 'ELEVENLABS_API_KEY', value: elevenKey })

      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const prov = PROVIDERS.find(p => p.id === provider)

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          onClick={onClose}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 200, backdropFilter: 'blur(2px)' }}
        />
      )}

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0,
        width: '360px', background: 'rgba(4,12,28,0.98)',
        borderLeft: '1px solid var(--border)',
        zIndex: 201, display: 'flex', flexDirection: 'column',
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.25s cubic-bezier(0.4,0,0.2,1)',
        backdropFilter: 'blur(20px)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          <span style={{ fontFamily: 'var(--display)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.25em', color: 'var(--cyan)' }}>SETTINGS</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: '14px', lineHeight: 1 }}>✕</button>
        </div>

        {/* Scrollable content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '4px 18px 24px', scrollbarWidth: 'thin', scrollbarColor: 'var(--border) transparent' }}>

          <SectionHeader label="LLM Provider" />

          <Field label="Provider">
            <Select
              value={provider}
              onChange={setProvider}
              options={PROVIDERS.map(p => ({ value: p.id, label: p.label }))}
            />
          </Field>

          <Field label={`${prov?.label} API Key`} hint="Leave blank to keep existing key">
            <Input
              type="password"
              value={apiKey}
              onChange={setApiKey}
              placeholder="paste key here..."
            />
          </Field>

          <Field label="Model">
            {provider === 'nvidia' && !useCustom ? (
              <Select
                value={model}
                onChange={setModel}
                options={NVIDIA_MODELS.map(m => ({ value: m, label: m }))}
              />
            ) : (
              <Input value={useCustom ? customModel : model} onChange={useCustom ? setCustomModel : setModel} placeholder="model name or ID" />
            )}
            <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }} onClick={() => setUseCustom(v => !v)}>
              <div style={{ width: '12px', height: '12px', border: `1px solid ${useCustom ? 'var(--cyan)' : 'var(--border)'}`, borderRadius: '2px', background: useCustom ? 'rgba(0,200,255,0.2)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {useCustom && <span style={{ color: 'var(--cyan)', fontSize: '9px', lineHeight: 1 }}>✓</span>}
              </div>
              <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.1em' }}>USE CUSTOM MODEL STRING</span>
            </div>
          </Field>

          <SectionHeader label="Voice Pipeline" />

          <Field label="Groq API Key (STT)" hint="Used for Whisper speech-to-text">
            <Input type="password" value={groqKey} onChange={setGroqKey} placeholder="gsk_..." />
          </Field>

          <Field label="ElevenLabs API Key (TTS)" hint="Used for FRIDAY voice output">
            <Input type="password" value={elevenKey} onChange={setElevenKey} placeholder="sk_..." />
          </Field>

          <Field label="ElevenLabs Voice ID" hint="Paste your custom FRIDAY voice ID">
            <Input value={elevenVoice} onChange={setElevenVoice} placeholder="abc123xyz..." />
          </Field>

          <SectionHeader label="Danger Zone" />

          <Field label="Auxiliary Provider" hint="Used for context compression & memory">
            <Select
              value={provider}
              onChange={v => post('/bridge/config', { key: 'auxiliary.provider', value: v }).catch(() => {})}
              options={PROVIDERS.filter(p => p.id !== 'ollama').map(p => ({ value: p.id, label: p.label }))}
            />
          </Field>

          {error && (
            <div style={{ fontFamily: 'var(--mono)', fontSize: '10px', color: 'var(--red)', background: 'rgba(255,64,96,0.1)', border: '1px solid rgba(255,64,96,0.2)', borderRadius: '3px', padding: '8px 10px', marginBottom: '14px' }}>
              ⚠ {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ borderTop: '1px solid var(--border)', padding: '12px 18px', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: 'var(--mono)', fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.08em' }}>Restart gateway after saving</span>
          <SaveBtn onClick={handleSave} saving={saving} saved={saved} />
        </div>
      </div>
    </>
  )
}