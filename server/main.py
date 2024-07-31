import asyncio
import socketio
import aiohttp_cors
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.sdp import candidate_from_sdp
from aiortc.contrib.media import MediaBlackhole
import numpy as np
from collections import deque

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])
app = web.Application()
sio.attach(app)

pc, blackholes = None, []
sids = []

class AudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        return frame

class OutputAudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.sample_rate = 48000
        self.frame_duration = 0.02  # 20ms
        self.frame_size = int(self.sample_rate * self.frame_duration)
        self.silence = np.zeros(self.frame_size, dtype=np.float32)  # 20ms of silence
        self.buffer = deque([self.silence] * (self.sample_rate // self.frame_size))

    async def recv(self):
        if not self.buffer:
            self.buffer.extend([self.silence] * (self.sample_rate // self.frame_size))
        frame = self.buffer.popleft()
        return frame

    async def inject_audio(self, audio_data):
        # Ensure audio_data is in frames
        num_frames = len(audio_data) // self.frame_size
        audio_frames = np.split(audio_data[:num_frames * self.frame_size], num_frames)
        for frame in audio_frames:
            self.buffer.append(frame)
            if len(self.buffer) > (self.sample_rate // self.frame_size):
                self.buffer.popleft()

def generate_sine_wave(frequency, duration, sample_rate=48000):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)

async def audio_injector(track):
    while True:
        await asyncio.sleep(5)
        sine_wave = generate_sine_wave(440, 2)  # 440 Hz for 2 seconds
        await track.inject_audio(sine_wave)

@sio.event
async def connect(sid, environ):
    global sids
    sids.append(sid)
    print('Client connected:', sid)

@sio.event
async def disconnect(sid):
    global sids
    sids.remove(sid)
    print('Client disconnected:', sid)

@sio.event
async def signal(sid, params):
    global pc
    if 'sdp' in params:
        offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

        if pc is None or pc.signalingState == "closed":
            create_peer_connection()

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await sio.emit('signal', {'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type})

    elif 'candidate' in params:
        candidate_dict = params['candidate']
        candidate = candidate_from_sdp(candidate_dict['candidate'])
        candidate.sdpMid = candidate_dict['sdpMid']
        candidate.sdpMLineIndex = candidate_dict['sdpMLineIndex']
        await pc.addIceCandidate(candidate)

async def on_shutdown(app):
    global sids
    for sid in sids:
        await sio.disconnect(sid)

def create_peer_connection():
    global pc, blackholes

    pc = RTCPeerConnection()
    blackholes = []

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print(f"ICE connection state is {pc.iceConnectionState}")

    @pc.on("track")
    async def on_track(track):
        print(f"Received track: {track.kind}")
        if track.kind == "audio":
            wrapped_track = AudioStreamTrack(track)
            pc.addTrack(wrapped_track)
            blackhole = MediaBlackhole()
            blackhole.addTrack(wrapped_track)
            await blackhole.start()
            blackholes.append(blackhole)

    # Add outgoing track for bidirectional audio
    output_track = OutputAudioStreamTrack()
    pc.addTrack(output_track)
    asyncio.ensure_future(audio_injector(output_track))

app.router.add_get('/', lambda request: web.Response(text="WebRTC Server"))
app.on_shutdown.append(on_shutdown)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

for route in app.router.routes():
    if route.resource.canonical == '/':
        cors.add(route)

if __name__ == '__main__':
    web.run_app(app, port=5000)
