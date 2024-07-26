import asyncio
import json
from aiohttp import web
import aiohttp_cors
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaBlackhole
# from google.cloud import speech_v1p1beta1 as speech
import socketio

# # Initialize Google Cloud Speech client
# speech_client = speech.SpeechClient()

# WebSocket server setup
sio = socketio.AsyncServer(async_mode='aiohttp')
app = web.Application()
sio.attach(app)

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
        audio_data = frame.to_ndarray().tobytes()
        # audio = speech.RecognitionAudio(content=audio_data)
        # config = speech.RecognitionConfig(
        #     encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        #     sample_rate_hertz=48000,
        #     language_code="en-US"
        # )
        # response = speech_client.recognize(config=config, audio=audio)
        # for result in response.results:
        #     transcription = result.alternatives[0].transcript
        #     await sio.emit('transcription', transcription)
        await sio.emit('transcription', "Hello there!")

@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

@sio.event
async def signal(sid, data):
    params = json.loads(data)
    if 'sdp' in params:
        offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await sio.emit('signal', json.dumps({'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type}))

    elif 'candidate' in params:
        candidate = params['candidate']
        await pc.addIceCandidate(candidate)

async def on_shutdown(app):
    await sio.disconnect()

# WebRTC setup
pc = RTCPeerConnection()
pc.addTrack(AudioStreamTrack(MediaBlackhole()))

# Web server setup
app.router.add_get('/', lambda request: web.Response(text="WebRTC Server"))
app.on_shutdown.append(on_shutdown)

# # CORS setup
# cors = aiohttp_cors.setup(app)
# for route in list(app.router.routes()):
#     cors.add(route, {
#         "*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")
#     })

if __name__ == '__main__':
    web.run_app(app, port=5000)
