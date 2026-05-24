import { useEffect, useRef } from 'react'

export type LogEntry = {
  id: number
  input: string
  success: boolean
  action?: string
  message: string
  ts: string
}

type Props = {
  log: LogEntry[]
}

export function ResponsePanel({ log }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log])

  if (log.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-zinc-600 select-none">
        <div className="text-4xl">🎛</div>
        <p className="text-sm">Type a command to control FL Studio</p>
        <div className="text-xs text-zinc-700 space-y-1 text-center mt-2">
          <p>"set bpm 140" · "play" · "stop"</p>
          <p>"mute channel 3" · "set volume channel 2 to 80"</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
      {log.map((entry) => (
        <div key={entry.id} className="group">
          <div className="flex items-baseline gap-2">
            <span className="text-xs text-zinc-600 tabular-nums shrink-0">{entry.ts}</span>
            <span className="text-sm text-zinc-200">
              <span className="text-accent">›</span> {entry.input}
            </span>
          </div>
          <div className={`ml-10 text-xs mt-0.5 ${entry.success ? 'text-green-400' : 'text-red-400'}`}>
            {entry.action && (
              <span className="text-zinc-500 mr-2">[{entry.action}]</span>
            )}
            {entry.message}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
