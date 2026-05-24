import { useState } from 'react'
import { useBackend } from './hooks/useBackend'
import { StatusPanel } from './components/StatusPanel/StatusPanel'
import { ResponsePanel, type LogEntry } from './components/ResponsePanel/ResponsePanel'
import { CommandBar } from './components/CommandBar/CommandBar'

let _id = 0

export default function App() {
  const { status, backendOnline, sendCommand } = useBackend()
  const [log, setLog] = useState<LogEntry[]>([])

  const handleCommand = async (text: string) => {
    const result = await sendCommand(text)
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false })
    setLog((prev) => [
      ...prev,
      { id: _id++, input: text, ts, ...result },
    ])
  }

  return (
    <div className="h-full flex flex-col bg-surface-900">
      <StatusPanel status={status} backendOnline={backendOnline} />
      <ResponsePanel log={log} />
      <CommandBar onSubmit={handleCommand} disabled={!backendOnline} />
    </div>
  )
}
