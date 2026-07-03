import { useState, useRef, useCallback } from 'react'

const API = 'http://127.0.0.1:8001'

/** Encode Float32 PCM samples as a 16-bit mono WAV file. */
function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)

  const writeStr = (offset: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i))
  }

  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)          // PCM
  view.setUint16(22, 1, true)          // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeStr(36, 'data')
  view.setUint32(40, samples.length * 2, true)

  let offset = 44
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  return new Blob([buffer], { type: 'audio/wav' })
}

export type VoiceState = 'idle' | 'recording' | 'transcribing'

export function useVoice(onTranscript: (text: string) => void) {
  const [state, setState] = useState<VoiceState>('idle')
  const [error, setError] = useState<string | null>(null)

  const streamRef = useRef<MediaStream | null>(null)
  const ctxRef = useRef<AudioContext | null>(null)
  const chunksRef = useRef<Float32Array[]>([])

  const start = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const ctx = new AudioContext({ sampleRate: 16000 })
      const source = ctx.createMediaStreamSource(stream)
      const processor = ctx.createScriptProcessor(4096, 1, 1)

      chunksRef.current = []
      processor.onaudioprocess = (e) => {
        chunksRef.current.push(new Float32Array(e.inputBuffer.getChannelData(0)))
      }
      source.connect(processor)
      processor.connect(ctx.destination)

      streamRef.current = stream
      ctxRef.current = ctx
      setState('recording')
    } catch {
      setError('Microphone access denied')
      setState('idle')
    }
  }, [])

  const stop = useCallback(async () => {
    const ctx = ctxRef.current
    const stream = streamRef.current
    if (!ctx || !stream) return

    stream.getTracks().forEach((t) => t.stop())
    const sampleRate = ctx.sampleRate
    await ctx.close()
    ctxRef.current = null
    streamRef.current = null

    const chunks = chunksRef.current
    const total = chunks.reduce((n, c) => n + c.length, 0)
    if (total < sampleRate / 4) {
      // Under a quarter second of audio — ignore.
      setState('idle')
      return
    }

    const samples = new Float32Array(total)
    let pos = 0
    for (const c of chunks) {
      samples.set(c, pos)
      pos += c.length
    }

    setState('transcribing')
    try {
      const wav = encodeWav(samples, sampleRate)
      const form = new FormData()
      form.append('file', wav, 'speech.wav')
      const res = await fetch(`${API}/audio/transcribe`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const { text } = await res.json()
      if (text) onTranscript(text)
      else setError('Nothing heard — try again')
    } catch {
      setError('Transcription failed')
    } finally {
      setState('idle')
    }
  }, [onTranscript])

  const toggle = useCallback(() => {
    if (state === 'recording') stop()
    else if (state === 'idle') start()
  }, [state, start, stop])

  return { state, error, toggle }
}
