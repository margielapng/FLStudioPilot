"""Offline speech-to-text using Vosk (local, no API key needed).

The small English model (~40 MB) is downloaded automatically to
~/.cache/vosk on first use.
"""

import io
import json
import wave

_MODEL_NAME = "vosk-model-small-en-us-0.15"
_model = None


def _get_model():
    global _model
    if _model is None:
        from vosk import Model
        _model = Model(model_name=_MODEL_NAME)
    return _model


def transcribe_wav(data: bytes) -> str:
    """Transcribe 16-bit mono PCM WAV bytes to text."""
    from vosk import KaldiRecognizer

    with wave.open(io.BytesIO(data), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("Expected 16-bit mono PCM WAV")
        rec = KaldiRecognizer(_get_model(), wf.getframerate())
        while True:
            frames = wf.readframes(4000)
            if not frames:
                break
            rec.AcceptWaveform(frames)

    result = json.loads(rec.FinalResult())
    return result.get("text", "").strip()
