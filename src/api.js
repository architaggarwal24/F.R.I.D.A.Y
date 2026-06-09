const HERMES_BASE = import.meta.env.VITE_HERMES_URL  || 'http://localhost:8642/v1'
const HERMES_KEY  = import.meta.env.VITE_HERMES_KEY  || 'friday-local-dev'
const MODEL       = import.meta.env.VITE_HERMES_MODEL || 'meta/llama-3.3-70b-instruct'

const SYSTEM_PROMPT = `You are FRIDAY (Fully Responsive Intelligence Digital Assistant Yeah), Tony Stark's AI. You are direct, highly capable, and slightly witty. You address the user as "boss". You are concise unless detail is needed. You never break character.`

// Map tool names to activity feed types
const TOOL_TYPE_MAP = {
  web_search:        'WEB',
  browser_navigate:  'WEB',
  browser_use:       'WEB',
  fetch_url:         'WEB',
  read_url:          'WEB',
  code_exec:         'TOOL',
  execute_command:   'TOOL',
  run_python:        'TOOL',
  file_read:         'TOOL',
  file_write:        'TOOL',
  file_list:         'TOOL',
  delegate_task:     'AGENT',
  spawn_agent:       'AGENT',
  skill_view:        'SKILL',
  skill_load:        'SKILL',
  skill_save:        'SKILL',
  memory_read:       'MEM',
  memory_write:      'MEM',
  memory_search:     'MEM',
}

function classifyTool(toolName) {
  if (!toolName) return 'TOOL'
  const lower = toolName.toLowerCase()
  for (const [key, type] of Object.entries(TOOL_TYPE_MAP)) {
    if (lower.includes(key)) return type
  }
  if (lower.includes('web') || lower.includes('search') || lower.includes('browse')) return 'WEB'
  if (lower.includes('agent') || lower.includes('delegate'))                          return 'AGENT'
  if (lower.includes('skill'))                                                         return 'SKILL'
  if (lower.includes('mem') || lower.includes('memory'))                              return 'MEM'
  return 'TOOL'
}

function extractToolDetail(toolName, argsStr) {
  if (!argsStr) return toolName
  try {
    const args = JSON.parse(argsStr)
    // Try common arg names for a meaningful preview
    const preview =
      args.query   || args.url      || args.command ||
      args.path    || args.filename || args.task    ||
      args.content || args.name     || args.text
    if (preview) return String(preview).slice(0, 45)
  } catch {}
  return toolName
}

export async function sendMessage(messages, onToken, onTool, onDone, onError) {
  const payload = {
    model: MODEL,
    stream: true,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages.map(m => ({
        role:    m.role === 'friday' ? 'assistant' : 'user',
        content: m.content,
      })),
    ],
  }

  try {
    const res = await fetch(`${HERMES_BASE}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${HERMES_KEY}`,
      },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const err = await res.text()
      onError(`Hermes error ${res.status}: ${err}`)
      return
    }

    const reader  = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer    = ''

    // Accumulate tool call args across chunks (streamed in pieces)
    const toolCallBuffer = {}  // index → { name, args }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data:')) continue
        const data = trimmed.slice(5).trim()
        if (data === '[DONE]') { onDone(); return }

        let json
        try { json = JSON.parse(data) } catch { continue }

        const delta = json.choices?.[0]?.delta

        // ── Text token ──────────────────────────────────────
        if (delta?.content) {
          onToken(delta.content)
        }

        // ── Tool call chunks ────────────────────────────────
        if (delta?.tool_calls) {
          for (const tc of delta.tool_calls) {
            const idx = tc.index ?? 0

            if (!toolCallBuffer[idx]) {
              toolCallBuffer[idx] = { name: '', args: '' }
            }

            if (tc.function?.name) {
              toolCallBuffer[idx].name += tc.function.name
            }
            if (tc.function?.arguments) {
              toolCallBuffer[idx].args += tc.function.arguments
            }

            // Fire event once we have a name (args may still be streaming)
            if (toolCallBuffer[idx].name && !toolCallBuffer[idx].fired) {
              toolCallBuffer[idx].fired = true
              const name   = toolCallBuffer[idx].name
              const type   = classifyTool(name)
              const detail = extractToolDetail(name, toolCallBuffer[idx].args)
              onTool?.({ type, label: name, detail, active: true })
            }
          }
        }

        // ── Finish reason: tool_calls complete ──────────────
        const finishReason = json.choices?.[0]?.finish_reason
        if (finishReason === 'tool_calls') {
          // Fire final events with full args for all buffered tools
          for (const [, tc] of Object.entries(toolCallBuffer)) {
            if (tc.name) {
              const type   = classifyTool(tc.name)
              const detail = extractToolDetail(tc.name, tc.args)
              onTool?.({ type, label: tc.name, detail, active: false })
            }
          }
        }
      }
    }
    onDone()
  } catch (err) {
    onError(err.message)
  }
}