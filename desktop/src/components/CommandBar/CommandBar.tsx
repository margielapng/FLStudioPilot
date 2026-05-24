import { useState, useRef, type KeyboardEvent } from 'react'

type Props = {
  onSubmit: (text: string) => Promise<void>
  disabled?: boolean
}

const SUGGESTIONS = [
  'set bpm 140',
  'play',
  'stop',
  'mute channel 1',
  'unmute channel 1',
  'set volume channel 2 to 85',
]

export function CommandBar({ onSubmit, disabled }: Props) {
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyIdx, setHistoryIdx] = useState(-1)
  const [history, setHistory] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const submit = async () => {
    const text = value.trim()
    if (!text || loading) return
    setLoading(true)
    setHistory((h) => [text, ...h.slice(0, 49)])
    setHistoryIdx(-1)
    setValue('')
    await onSubmit(text)
    setLoading(false)
    inputRef.current?.focus()
  }

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') { submit(); return }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      const next = Math.min(historyIdx + 1, history.length - 1)
      setHistoryIdx(next)
      setValue(history[next] ?? '')
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      const next = Math.max(historyIdx - 1, -1)
      setHistoryIdx(next)
      setValue(next === -1 ? '' : history[next])
    }
  }

  return (
    <div className="border-t border-surface-600 bg-surface-800 p-3 space-y-2">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-accent text-sm select-none">›_</span>
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKey}
            disabled={disabled || loading}
            placeholder={disabled ? 'Backend offline…' : 'Tell FL Studio what to do…'}
            className="w-full pl-8 pr-3 py-2.5 bg-surface-700 border border-surface-600 rounded-lg
                       text-sm text-zinc-100 placeholder-zinc-600 outline-none
                       focus:border-accent focus:ring-1 focus:ring-accent/30
                       disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            autoFocus
          />
        </div>
        <button
          onClick={submit}
          disabled={disabled || loading || !value.trim()}
          className="px-4 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-40
                     disabled:cursor-not-allowed rounded-lg text-sm font-semibold
                     transition-colors text-white"
        >
          {loading ? '…' : 'Send'}
        </button>
      </div>

      <div className="flex gap-1.5 flex-wrap">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => { setValue(s); inputRef.current?.focus() }}
            className="text-xs px-2 py-0.5 rounded bg-surface-700 text-zinc-500
                       hover:text-zinc-300 hover:bg-surface-600 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
