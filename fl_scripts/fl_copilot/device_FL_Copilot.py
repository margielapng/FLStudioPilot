"""
FL Copilot Bridge — runs inside FL Studio as a MIDI Controller Script.

Install location:
  C:\Users\<you>\Documents\Image-Line\FL Studio\Settings\Hardware\FL_Copilot\

Activate in FL Studio:
  Options → MIDI Settings → enable this script on any controller port.
"""

import channels
import mixer
import transport
import ui
import patterns
import playlist
import socket
import json
import threading
import queue
import time

NAME = "FL Copilot"
VERSION = "0.1.0"

HOST = "127.0.0.1"
PORT = 9877

# Queue of (connection, command_dict) from the socket thread → OnIdle processes
_cmd_queue: queue.Queue = queue.Queue()
_server_sock: socket.socket | None = None
_running = False


# ── FL Studio lifecycle callbacks ──────────────────────────────────────────────

def OnInit():
    global _server_sock, _running
    _running = True
    _server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _server_sock.settimeout(0)  # non-blocking
    try:
        _server_sock.bind((HOST, PORT))
        _server_sock.listen(8)
        threading.Thread(target=_accept_loop, daemon=True).start()
        ui.setHintMsg(f"FL Copilot bridge listening on port {PORT}")
        print(f"[FL Copilot] Bridge started on {HOST}:{PORT}")
    except OSError as e:
        ui.setHintMsg(f"FL Copilot: port {PORT} unavailable — {e}")
        print(f"[FL Copilot] Failed to bind: {e}")


def OnDeInit():
    global _running
    _running = False
    if _server_sock:
        try:
            _server_sock.close()
        except Exception:
            pass
    print("[FL Copilot] Bridge stopped")


def OnIdle():
    """Called periodically by FL Studio — drain the command queue here."""
    processed = 0
    while processed < 10:  # cap per idle tick to keep FL Studio responsive
        try:
            conn, cmd = _cmd_queue.get_nowait()
        except queue.Empty:
            break
        response = _execute(cmd)
        _send(conn, response)
        processed += 1


def OnMidiMsg(event):
    event.handled = False  # pass MIDI through to FL Studio normally


# ── Socket server (background thread) ─────────────────────────────────────────

def _accept_loop():
    while _running:
        try:
            conn, _ = _server_sock.accept()
            threading.Thread(target=_read_client, args=(conn,), daemon=True).start()
        except BlockingIOError:
            time.sleep(0.01)
        except OSError:
            break


def _read_client(conn: socket.socket):
    try:
        buf = b""
        conn.settimeout(5.0)
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
            if b"\n" in buf:
                break
        line = buf.split(b"\n")[0].strip()
        if line:
            cmd = json.loads(line.decode())
            _cmd_queue.put((conn, cmd))
        # conn stays open — OnIdle sends the reply and closes it
    except Exception as e:
        _send(conn, {"ok": False, "error": str(e)})


def _send(conn: socket.socket, data: dict):
    try:
        conn.sendall((json.dumps(data) + "\n").encode())
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── Command execution (runs on FL Studio main thread via OnIdle) ───────────────

def _execute(cmd: dict) -> dict:
    action = cmd.get("action", "")
    params = cmd.get("params", {})
    try:
        return _HANDLERS[action](params)
    except KeyError:
        return {"ok": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _h_get_status(_p):
    return {
        "ok": True,
        "connected": True,
        "fl_version": str(ui.getVersion()),
        "project_name": ui.getProjectName(),
        "bpm": transport.getTempo(),
        "playing": transport.isPlaying(),
    }


def _h_play(_p):
    transport.start()
    return {"ok": True, "message": "Playback started"}


def _h_stop(_p):
    transport.stop()
    return {"ok": True, "message": "Playback stopped"}


def _h_set_bpm(p):
    bpm = float(p.get("value", 120))
    bpm = max(10.0, min(999.0, bpm))
    transport.setTempo(bpm)
    return {"ok": True, "message": f"BPM set to {bpm}"}


def _h_mute_channel(p):
    idx = int(p.get("channel", 0))
    if not channels.isChannelMuted(idx):
        channels.muteChannel(idx)
    name = channels.getChannelName(idx)
    return {"ok": True, "message": f'"{name}" muted'}


def _h_unmute_channel(p):
    idx = int(p.get("channel", 0))
    if channels.isChannelMuted(idx):
        channels.muteChannel(idx)
    name = channels.getChannelName(idx)
    return {"ok": True, "message": f'"{name}" unmuted'}


def _h_set_channel_volume(p):
    idx = int(p.get("channel", 0))
    pct = float(p.get("volume", 80))
    # FL channel volume: 0.0–1.25 (100% = 1.0)
    vol = max(0.0, min(1.25, pct / 100.0))
    channels.setChannelVolume(idx, vol)
    name = channels.getChannelName(idx)
    return {"ok": True, "message": f'"{name}" volume → {pct}%'}


def _h_set_mixer_volume(p):
    track = int(p.get("track", 1))
    pct = float(p.get("volume", 80))
    vol = max(0.0, min(1.25, pct / 100.0))
    mixer.setTrackVolume(track, vol)
    name = mixer.getTrackName(track)
    return {"ok": True, "message": f'Mixer "{name}" volume → {pct}%'}


def _h_select_channel(p):
    idx = int(p.get("channel", 0))
    channels.selectChannel(idx, 1)
    name = channels.getChannelName(idx)
    return {"ok": True, "message": f'"{name}" selected'}


_HANDLERS = {
    "get_status":          _h_get_status,
    "play":                _h_play,
    "stop":                _h_stop,
    "set_bpm":             _h_set_bpm,
    "mute_channel":        _h_mute_channel,
    "unmute_channel":      _h_unmute_channel,
    "set_channel_volume":  _h_set_channel_volume,
    "set_mixer_volume":    _h_set_mixer_volume,
    "select_channel":      _h_select_channel,
}
