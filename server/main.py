import asyncio
import json
import socketio
import aiohttp_cors
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.sdp import candidate_from_sdp
from aiortc.contrib.media import MediaBlackhole
from pprint import pprint


sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])
app = web.Application()
sio.attach(app)

pc, blackholes = None, []
counter = 0
sids = []


class AudioStreamTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track):
        super().__init__()
        self.track = track
        self.stopped = False

    async def recv(self):
        frame = await self.track.recv()
        if not self.stopped:
            await self.send_to_stt(frame)
        return frame

    async def send_to_stt(self, frame):
        global counter
        counter += 1
        if (counter % 100 == 0):
            await sio.emit('transcription', "Hello there!")

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
