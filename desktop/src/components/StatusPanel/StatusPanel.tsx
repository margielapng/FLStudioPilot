import type { FLStatus } from '../../hooks/useBackend'

type Props = {
  status: FLStatus | null
  backendOnline: boolean
}

export function StatusPanel({ status, backendOnline }: Props) {
  const dot = (on: boolean, label: string) => (
    <div className="flex items-center gap-1.5">
      <span className={`w-1.5 h-1.5 rounded-full ${on ? 'bg-green-400' : 'bg-red-500'}`} />
      <span className="text-xs text-zinc-400">{label}</span>
    </div>
  )

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-surface-800 border-b border-surface-600">
      <span className="text-xs font-semibold text-accent tracking-widest uppercase">FL Copilot</span>
      <div className="flex items-center gap-4 ml-auto">
        {dot(backendOnline, 'Backend')}
        {dot(status?.connected ?? false, 'FL Studio')}
        {status?.bpm !== undefined && (
          <span className="text-xs text-zinc-300 tabular-nums">{status.bpm} BPM</span>
        )}
        {status?.playing !== undefined && (
          <span className={`text-xs ${status.playing ? 'text-green-400' : 'text-zinc-500'}`}>
            {status.playing ? '▶ Playing' : '■ Stopped'}
          </span>
        )}
      </div>
    </div>
  )
}
