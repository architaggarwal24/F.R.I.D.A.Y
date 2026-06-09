"""
FRIDAY Voice Pipeline
─────────────────────
HTTP  POST /trigger  → start recording (from MIC button)
Groq Whisper         → speech to text
WebSocket            → syncs state with UI / receives TTS requests
ElevenLabs + pygame  → text to speech playback
"""

import asyncio
import json
import os
import sys
import tempfile
import threading
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler

import numpy as np
import pyaudio
import websockets
from dotenv import load_dotenv
from groq import Groq
from elevenlabs.client import ElevenLabs
import pygame

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ── Config ────────────────────────────────────────────────
GROQ_API_KEY    = os.getenv('GROQ_API_KEY')
ELEVEN_API_KEY  = os.getenv('ELEVENLABS_API_KEY')
ELEVEN_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')
WS_PORT         = int(os.getenv('VOICE_WS_PORT',     '5175'))
HTTP_PORT       = int(os.getenv('VOICE_HTTP_PORT',   '5176'))
SAMPLE_RATE     = 16000
CHUNK           = 1280
RECORD_SECONDS  = int(os.getenv('RECORD_SECONDS',    '6'))
MIC_INDEX       = int(os.getenv('MIC_DEVICE_INDEX',  '15'))

# ── Clients ───────────────────────────────────────────────
groq_client   = Groq(api_key=GROQ_API_KEY)
eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)
pygame.mixer.init()

# ── Shared state ──────────────────────────────────────────
connected_clients = set()
_loop             = None
_is_recording     = False   # guard against concurrent recordings

# ── Broadcast to all UI clients ───────────────────────────
def broadcast(msg: dict):
    if not connected_clients or _loop is None:
        return
    data = json.dumps(msg)
    _loop.call_soon_threadsafe(
        lambda: _loop.create_task(_broadcast(data))
    )

async def _broadcast(data: str):
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send(data)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)

# ── WebSocket server ──────────────────────────────────────
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f'[WS] UI connected ({len(connected_clients)} clients)')
    try:
        await websocket.send(json.dumps({'type': 'state', 'state': 'idle', 'wakeWordOn': False}))
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'tts':
                    threading.Thread(target=speak, args=(data['text'],), daemon=True).start()
            except Exception:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f'[WS] UI disconnected ({len(connected_clients)} clients)')

# ── Audio helpers ─────────────────────────────────────────
def record_audio() -> bytes:
    """Record from mic until silence or max duration."""
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16, channels=1,
        rate=SAMPLE_RATE, input=True,
        input_device_index=MIC_INDEX,
        frames_per_buffer=CHUNK,
    )
    frames        = []
    total_chunks  = int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)
    silence_count = 0
    print(f'[MIC] Recording (max {RECORD_SECONDS}s)...')

    for _ in range(total_chunks):
        data   = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        energy = np.sqrt(np.mean(np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2))
        if len(frames) > 8:
            silence_count = silence_count + 1 if energy < 200 else 0
            if silence_count >= 6:
                break

    stream.stop_stream()
    stream.close()
    pa.terminate()
    print(f'[MIC] Done — {len(frames)} chunks captured')
    return b''.join(frames)

def pcm_to_wav(pcm_bytes: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    with wave.open(tmp.name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)
    return tmp.name

def transcribe(wav_path: str) -> str:
    with open(wav_path, 'rb') as f:
        result = groq_client.audio.transcriptions.create(
            file=(os.path.basename(wav_path), f),
            model='whisper-large-v3-turbo',
            language='en',
        )
    return result.text.strip()

def speak(text: str):
    print(f'[TTS] Speaking: {text[:70]}')
    broadcast({'type': 'state', 'state': 'speaking'})
    try:
        audio_bytes = b''.join(
            eleven_client.text_to_speech.convert(
                voice_id=ELEVEN_VOICE_ID,
                text=text,
                model_id='eleven_turbo_v2_5',
                output_format='mp3_44100_128',
            )
        )
        tmp_path = tempfile.mktemp(suffix='.mp3')
        with open(tmp_path, 'wb') as f:
            f.write(audio_bytes)
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
    except Exception as e:
        print(f'[TTS] Error: {e}')
    finally:
        broadcast({'type': 'state', 'state': 'idle'})

# ── Recording pipeline (called by HTTP trigger or wake word) ─
def run_recording_pipeline():
    global _is_recording
    if _is_recording:
        print('[MIC] Already recording, ignoring trigger')
        return
    _is_recording = True
    try:
        broadcast({'type': 'state', 'state': 'listening'})
        pcm  = record_audio()
        broadcast({'type': 'state', 'state': 'thinking'})
        wav  = pcm_to_wav(pcm)
        text = transcribe(wav)
        os.unlink(wav)
        print(f'[STT] "{text}"')
        if text:
            broadcast({'type': 'voice_input', 'text': text})
        else:
            broadcast({'type': 'state', 'state': 'idle'})
    except Exception as e:
        print(f'[PIPELINE] Error: {e}')
        broadcast({'type': 'state', 'state': 'error'})
    finally:
        _is_recording = False

# ── HTTP server for MIC button trigger ────────────────────
class TriggerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/trigger':
            threading.Thread(target=run_recording_pipeline, daemon=True).start()
            self._respond(200, {'ok': True})
        else:
            self._respond(404, {'error': 'not found'})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _respond(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type',   'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *args):
        pass  # silence HTTP logs

def start_http_server():
    server = HTTPServer(('localhost', HTTP_PORT), TriggerHandler)
    print(f'[HTTP] Trigger server on http://localhost:{HTTP_PORT}/trigger')
    server.serve_forever()

# ── Entry point ───────────────────────────────────────────
async def main():
    print('╔══════════════════════════════╗')
    print('║   FRIDAY Voice Pipeline      ║')
    print('╠══════════════════════════════╣')
    print(f'║  WS    → ws://localhost:{WS_PORT}   ║')
    print(f'║  HTTP  → localhost:{HTTP_PORT}/trigger ║')
    print(f'║  STT   → Groq Whisper        ║')
    print(f'║  TTS   → ElevenLabs          ║')
    print(f'║  Mic   → device {MIC_INDEX}            ║')
    print('╚══════════════════════════════╝')

    global _loop
    _loop = asyncio.get_event_loop()

    # HTTP trigger server in background thread
    threading.Thread(target=start_http_server, daemon=True).start()

    # WebSocket server (main async loop)
    async with websockets.serve(ws_handler, 'localhost', WS_PORT):
        print(f'[WS] Server ready on ws://localhost:{WS_PORT}')
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main()) 