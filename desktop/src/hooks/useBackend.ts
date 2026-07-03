import { useState, useEffect, useCallback } from 'react'

const API = 'http://127.0.0.1:8001'
const WS_URL = 'ws://127.0.0.1:8001/ws'

export type FLStatus = {
  connected: boolean
  fl_version?: string
  project_name?: string
  bpm?: number
  playing?: boolean
}

export type CommandResult = {
  success: boolean
  action?: string
  message: string
}

export function useBackend() {
  const [status, setStatus] = useState<FLStatus | null>(null)
  const [backendOnline, setBackendOnline] = useState(false)

  useEffect(() => {
    // Check if backend is up
    fetch(`${API}/health`)
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false))

    // WebSocket for live status updates
    let ws: WebSocket
    let retryTimer: ReturnType<typeof setTimeout>

    const connect = () => {
      ws = new WebSocket(WS_URL)
      ws.onopen = () => setBackendOnline(true)
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.type === 'status') setStatus(msg.data)
      }
      ws.onclose = () => {
        setBackendOnline(false)
        retryTimer = setTimeout(connect, 3000)
      }
    }

    connect()
    return () => {
      ws?.close()
      clearTimeout(retryTimer)
    }
  }, [])

  const sendCommand = useCallback(async (text: string): Promise<CommandResult> => {
    try {
      const res = await fetch(`${API}/commands/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      return await res.json()
    } catch {
      return { success: false, message: 'Backend offline — is the server running?' }
    }
  }, [])

  return { status, backendOnline, sendCommand }
}
