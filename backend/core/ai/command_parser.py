import json
from anthropic import AsyncAnthropic

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


_SYSTEM = """You are a command parser for FL Studio music production software.
Convert the user's natural language input into a JSON command object.

Available actions and their params:
- play               → {}
- stop               → {}
- set_bpm            → {"value": <float, 20–999>}
- mute_channel       → {"channel": <int, 0-indexed>}
- unmute_channel     → {"channel": <int, 0-indexed>}
- set_channel_volume → {"channel": <int, 0-indexed>, "volume": <int, 0–100>}
- set_mixer_volume   → {"track": <int, 1-indexed>, "volume": <int, 0–100>}
- select_channel     → {"channel": <int, 0-indexed>}

Channel numbers: user says "channel 1" → use 0 in params, "channel 3" → 2.
Mixer tracks stay 1-indexed.

Respond with ONLY a JSON object: {"action": "<action>", "params": {...}}
If the input doesn't match any action, respond with exactly: null"""


async def parse_command(text: str) -> dict | None:
    try:
        response = await _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=128,
            system=[{
                "type": "text",
                "text": _SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": text}],
        )
        raw = response.content[0].text.strip()
        if raw.lower() == "null":
            return None
        return json.loads(raw)
    except Exception:
        return None
