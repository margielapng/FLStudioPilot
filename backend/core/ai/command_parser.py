import re
from typing import Any


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


# (keywords, action, param extractor)
# Checked in order — first match wins.
_RULES = [
    (["play", "start"],                        "play",               lambda t: {}),
    (["stop", "pause"],                        "stop",               lambda t: {}),
    (["bpm", "tempo", "beat"],                 "set_bpm",            _parse_bpm),
    (["unmute", "un-mute"],                    "unmute_channel",     _parse_channel),
    (["mute"],                                 "mute_channel",       _parse_channel),
    (["volume", "vol", "louder", "quieter"],   "set_channel_volume", _parse_volume),
]


def parse_command(text: str) -> dict[str, Any] | None:
    lower = text.lower()
    for keywords, action, extractor in _RULES:
        if any(kw in lower for kw in keywords):
            return {"action": action, "params": extractor(lower)}
    return None
