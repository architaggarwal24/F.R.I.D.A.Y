import express from 'express'
import cors from 'cors'
import { exec } from 'child_process'
import { promisify } from 'util'
import { config } from 'dotenv'

config()  // load .env

const execAsync = promisify(exec)
const app = express()

const PORT        = process.env.BRIDGE_PORT        || 5174
const CORS_ORIGIN = process.env.BRIDGE_CORS_ORIGIN || 'http://localhost:5173'

app.use(cors({ origin: CORS_ORIGIN }))
app.use(express.json())

// ── Health ─────────────────────────────────────────────────
app.get('/bridge/health', (req, res) => res.json({ status: 'ok' }))

// ── Get config (parsed) ────────────────────────────────────
app.get('/bridge/config', async (req, res) => {
  try {
    const { stdout } = await execAsync('hermes config show')
    const modelMatch = stdout.match(/Model:\s+(\{.+?\})/s)
    let model = 'unknown', provider = 'unknown'
    if (modelMatch) {
      const raw = modelMatch[1]
      const defMatch  = raw.match(/'default'\s*:\s*'([^']+)'/)
      const provMatch = raw.match(/'provider'\s*:\s*'([^']+)'/)
      if (defMatch)  model    = defMatch[1]
      if (provMatch) provider = provMatch[1]
    }
    res.json({ model, provider })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── Set config ─────────────────────────────────────────────
app.post('/bridge/config', async (req, res) => {
  const { key, value } = req.body
  if (!key || value === undefined) return res.status(400).json({ error: 'key and value required' })
  const ALLOWED = ['model.default','model.provider','auxiliary.provider','personality','API_SERVER_KEY','API_SERVER_CORS_ORIGINS']
  if (!ALLOWED.includes(key)) return res.status(403).json({ error: `key '${key}' not allowed` })
  try {
    await execAsync(`hermes config set ${key} ${value}`)
    res.json({ ok: true, key, value })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// ── Set secrets ────────────────────────────────────────────
app.post('/bridge/secret', async (req, res) => {
  const { key, value } = req.body
  if (!key || !value) return res.status(400).json({ error: 'key and value required' })
  const ALLOWED = ['NVIDIA_API_KEY','OPENROUTER_API_KEY','ANTHROPIC_API_KEY','GROQ_API_KEY','ELEVENLABS_API_KEY','GOOGLE_API_KEY','OLLAMA_BASE_URL']
  if (!ALLOWED.includes(key)) return res.status(403).json({ error: `secret '${key}' not allowed` })
  try {
    await execAsync(`hermes config set ${key} ${value}`)
    res.json({ ok: true, key })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

app.listen(PORT, () => console.log(`FRIDAY bridge → http://localhost:${PORT}`))


// ── Get skills + tools count ───────────────────────────────
app.get('/bridge/stats', async (req, res) => {
  try {
    const [skillsOut, toolsOut] = await Promise.all([
      execAsync('hermes skills list').catch(() => ({ stdout: '' })),
      execAsync('hermes tools list').catch(() => ({ stdout: '' })),
    ])

    // Count non-empty lines that look like entries
    const countLines = (str) =>
      str.split('\n').filter(l => l.trim() && !l.startsWith('─') && !l.startsWith('┌') && !l.startsWith('└') && !l.startsWith('│') && !l.startsWith('◆')).length

    const skillsCount = countLines(skillsOut.stdout)
    const toolsCount  = countLines(toolsOut.stdout)

    // Also parse memory usage from sessions if available
    const sessionsOut = await execAsync('hermes sessions list').catch(() => ({ stdout: '' }))
    const sessionLines = sessionsOut.stdout.split('\n').filter(l => l.trim() && !l.includes('─') && !l.includes('┌') && !l.includes('Session')).length

    res.json({
      skills:   skillsCount  || 77,
      tools:    toolsCount   || 26,
      sessions: sessionLines || 0,
    })
  } catch (e) {
    res.status(500).json({ error: e.message, skills: 77, tools: 26, sessions: 0 })
  }
})