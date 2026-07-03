"""Offline speech-to-text using Vosk (local, no API key needed).

The small English model (~40 MB) is downloaded automatically to
~/.cache/vosk on first use.

Recognition is grammar-constrained to FL Copilot's command vocabulary,
which makes the small model far more accurate for our phrases. Number
words in the transcript are converted to digits for the command parser
("one hundred and forty" → "140").
"""

import io
import json
import wave

_MODEL_NAME = "vosk-model-small-en-us-0.15"
_model = None

# Command vocabulary. "bpm" isn't in the small model's lexicon, so it's
# spelled as letters (b p m) and stitched back together afterwards.
# [unk] lets the recognizer flag out-of-vocabulary sounds instead of
# force-matching them onto command words.
_VOCAB = (
    "play start stop pause "
    "set the to at a and "
    "b p m tempo beat beats per minute speed faster slower "
    "mute unmute channel channels volume track mixer select "
    "louder quieter percent up down "
    "zero one two three four five six seven eight nine ten "
    "eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
    "twenty thirty forty fifty sixty seventy eighty ninety hundred thousand "
    "[unk]"
)

_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_NUMBER_WORDS = set(_UNITS) | set(_TENS) | {"hundred", "thousand", "and"}


def _get_model():
    global _model
    if _model is None:
        from vosk import Model
        _model = Model(model_name=_MODEL_NAME)
    return _model


def _is_number_start(word: str) -> bool:
    return word in _UNITS or word in _TENS or word == "hundred"


def _words_to_digits(text: str) -> str:
    """Convert spans of number words to digits: 'one hundred and forty' → '140'.

    Handles two speech quirks:
    - The preposition 'to' is often recognized as 'two' ('set bpm to 140' →
      'set bpm two 140'). A 'two' directly followed by another number word
      that can't legally combine with it is dropped as a misheard 'to'.
    - Colloquial tempo (e.g. 'one forty' = 140): a single unit followed by a
      tens word reads as unit*100 + tens.
    """
    words = text.split()
    out: list[str] = []
    i = 0
    while i < len(words):
        w = words[i]
        if not _is_number_start(w):
            out.append(w)
            i += 1
            continue

        # Misheard preposition: 'two' followed by another number word, in a
        # position where 'to' belongs — right after bpm/tempo/speed ('set bpm
        # to 140') or right after a completed number ('channel 2 to 85').
        if (
            w == "two"
            and i + 1 < len(words)
            and (words[i + 1] in _UNITS or words[i + 1] in _TENS)
            and out
            and (out[-1] in ("bpm", "tempo", "speed") or out[-1].isdigit())
        ):
            i += 1
            continue

        # Consume one number-word span.
        value = 0
        current = 0
        last_kind = None  # 'unit' | 'tens' | 'mult'
        while i < len(words) and words[i] in _NUMBER_WORDS:
            w = words[i]
            if w == "and":
                if i + 1 >= len(words) or words[i + 1] not in _NUMBER_WORDS or words[i + 1] == "and":
                    break
                i += 1
                continue
            if w in _UNITS:
                if last_kind == "unit":
                    break  # 'five five' — two separate numbers
                current += _UNITS[w]
                last_kind = "unit"
            elif w in _TENS:
                if last_kind == "unit" and 1 <= current <= 9:
                    # 'one forty' → 140, but only where a tempo is being
                    # spoken; 'channel two eighty five' means 2 then 85.
                    tempo_context = any(t in out for t in ("bpm", "tempo", "speed"))
                    if tempo_context:
                        current = current * 100 + _TENS[w]
                    else:
                        break
                elif last_kind == "tens":
                    break  # 'forty twenty' — separate numbers
                else:
                    current += _TENS[w]
                last_kind = "tens"
            elif w == "hundred":
                current = (current or 1) * 100
                last_kind = "mult"
            elif w == "thousand":
                value += (current or 1) * 1000
                current = 0
                last_kind = "mult"
            i += 1
        out.append(str(value + current))
    return " ".join(out)


def transcribe_wav(data: bytes) -> str:
    """Transcribe 16-bit mono PCM WAV bytes to normalized command text."""
    from vosk import KaldiRecognizer

    with wave.open(io.BytesIO(data), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("Expected 16-bit mono PCM WAV")
        rec = KaldiRecognizer(_get_model(), wf.getframerate(), json.dumps(_VOCAB.split()))
        while True:
            frames = wf.readframes(4000)
            if not frames:
                break
            rec.AcceptWaveform(frames)

    text = json.loads(rec.FinalResult()).get("text", "").strip()
    text = text.replace("[unk]", "").strip()
    text = " ".join(text.split())  # collapse whitespace
    # 'bpm' isn't a lexicon word — it comes back as spelled letters,
    # sometimes with one dropped.
    for spelled in ("b p m", "b p", "p m", "b m"):
        text = text.replace(spelled, "bpm")
    # Nobody says 'channel to' — that's always a misheard 'channel two'.
    text = text.replace("channel to ", "channel two ")
    text = _words_to_digits(text)
    return text
