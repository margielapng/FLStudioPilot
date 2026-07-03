"""Command parser: keyword rules first (free, instant), Claude API as an
optional upgrade for natural language when an API key + credits exist."""

import json
import os
import re
from typing import Any

# ── Keyword parser (always available) ──────────────────────────────────────────

def _parse_bpm(text: str) -> dict[str, Any]:
    nums = re.findall(r"\d+\.?\d*", text)
    return {"value": float(nums[0])} if nums else {"value": 120.0}


def _parse_channel(text: str) -> dict[str, Any]:
    nums = re.findall(r"\d+", text)
    return {"channel": int(nums[0]) - 1} if nums else {"channel": 0}


def _parse_volume(text: str) -> dict[str, Any]:
    channel_nums = re.findall(r"channel\s*(\d+)", text, re.IGNORECASE)
    all_nums = re.findall(r"\d+", text)
    return {
        "channel": int(channel_nums[0]) - 1 if channel_nums else 0,
        "volume": int(all_nums[-1]) if all_nums else 80,
    }


# (keywords, action, param extractor) — first match wins.
_RULES = [
    (["play", "start"],                        "play",               lambda t: {}),
    (["stop", "pause"],                        "stop",               lambda t: {}),
    (["bpm", "tempo", "beat", "faster", "slower"], "set_bpm",        _parse_bpm),
    (["unmute", "un-mute"],                    "unmute_channel",     _parse_channel),
    (["mute"],                                 "mute_channel",       _parse_channel),
    (["volume", "vol", "louder", "quieter"],   "set_channel_volume", _parse_volume),
    (["select"],                               "select_channel",     _parse_channel),
]


def _keyword_parse(text: str) -> dict[str, Any] | None:
    lower = text.lower()
    for keywords, action, extractor in _RULES:
        if any(kw in lower for kw in keywords):
            return {"action": action, "params": extractor(lower)}
    return None


# ── Claude parser (optional — used only when a key is configured) ──────────────

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

_client = None
_claude_disabled = False  # set True after an auth/credit failure so we stop retrying


def _claude_available() -> bool:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return bool(key) and key != "your_key_here" and not _claude_disabled


async def _claude_parse(text: str) -> dict | None:
    global _client, _claude_disabled
    try:
        if _client is None:
            from anthropic import AsyncAnthropic
            _client = AsyncAnthropic()
        response = await _client.messages.create(
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
    except Exception as e:
        # Auth or billing errors won't fix themselves — fall back to keywords
        # permanently for this session instead of paying the latency every call.
        name = type(e).__name__
        if name in ("AuthenticationError", "PermissionDeniedError", "BadRequestError"):
            _claude_disabled = True
        return None


# ── Public API ──────────────────────────────────────────────────────────────────

async def parse_command(text: str) -> dict | None:
    result = _keyword_parse(text)
    if result:
        return result
    if _claude_available():
        return await _claude_parse(text)
    return None
