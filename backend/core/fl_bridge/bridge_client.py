import asyncio
import json
import os
from typing import Any

FL_HOST = os.getenv("FL_BRIDGE_HOST", "127.0.0.1")
FL_PORT = int(os.getenv("FL_BRIDGE_PORT", "9877"))

# Set FL_MOCK=false in .env once FL Studio is installed and the script is active.
_MOCK = os.getenv("FL_MOCK", "true").lower() not in ("false", "0", "no")

_MOCK_STATE: dict[str, Any] = {
    "connected": True,
    "fl_version": "FL Studio 21 (mock)",
    "project_name": "Untitled (mock)",
    "bpm": 140.0,
    "playing": False,
}


async def send_command(action: str, params: dict[str, Any] | None = None) -> dict:
    if _MOCK:
        return await _mock_command(action, params or {})
    return await _real_command(action, params or {})


async def get_status() -> dict:
    if _MOCK:
        return _MOCK_STATE.copy()
    result = await _real_command("get_status", {})
    return result if result.get("ok") else {
        "connected": False,
        "error": result.get("error", "FL Studio unreachable"),
    }


# ── Real FL Studio connection ──────────────────────────────────────────────────

async def _real_command(action: str, params: dict) -> dict:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(FL_HOST, FL_PORT), timeout=3.0
        )
        payload = json.dumps({"action": action, "params": params}) + "\n"
        writer.write(payload.encode())
        await writer.drain()
        line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        writer.close()
        await writer.wait_closed()
        return json.loads(line.decode())
    except asyncio.TimeoutError:
        return {"ok": False, "error": "FL Studio timed out — is the bridge script active?"}
    except (ConnectionRefusedError, OSError):
        return {"ok": False, "error": "FL Studio not connected — open FL Studio and enable the script"}


# ── Mock FL Studio (development without FL Studio installed) ───────────────────

async def _mock_command(action: str, params: dict) -> dict:
    await asyncio.sleep(0.04)  # simulate round-trip

    handlers = {
        "play":               lambda p: (_setstate("playing", True),  {"ok": True, "message": "Playback started"})[1],
        "stop":               lambda p: (_setstate("playing", False), {"ok": True, "message": "Playback stopped"})[1],
        "set_bpm":            lambda p: (_setstate("bpm", float(p.get("value", _MOCK_STATE["bpm"]))), {"ok": True, "message": f"BPM set to {_MOCK_STATE['bpm']}"})[1],
        "mute_channel":       lambda p: {"ok": True, "message": f"Channel {p.get('channel', 0) + 1} muted"},
        "unmute_channel":     lambda p: {"ok": True, "message": f"Channel {p.get('channel', 0) + 1} unmuted"},
        "set_channel_volume": lambda p: {"ok": True, "message": f"Channel {p.get('channel', 0) + 1} volume → {p.get('volume', 80)}%"},
        "set_mixer_volume":   lambda p: {"ok": True, "message": f"Mixer track {p.get('track', 1)} volume → {p.get('volume', 80)}%"},
        "select_channel":     lambda p: {"ok": True, "message": f"Channel {p.get('channel', 0) + 1} selected"},
        "get_status":         lambda p: _MOCK_STATE.copy(),
    }

    handler = handlers.get(action)
    if handler:
        return handler(params)
    return {"ok": True, "message": f"Mock: {action} executed"}


def _setstate(key: str, value: Any) -> None:
    _MOCK_STATE[key] = value
