import asyncio
import numpy as np
import aiohttp_cors
from aiohttp import web
import socketio
from agent import AudioAgent

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])
app = web.Application()
sio.attach(app)

output_audio_streams = {}
audio_agents = {}


class OutputAudioStream:
    def __init__(self):
        print("Initializing output audio stream")

        self.lock = asyncio.Lock()

        self.sample_rate = 8000
        self.frame_duration = 0.1
        self.frame_size = int(self.sample_rate * self.frame_duration)

        self.injected_audio = None
        self.injected_audio_index = 0

    async def get_audio_frame(self):
        async with self.lock:
            if self.injected_audio is not None:
                if (self.injected_audio_index + 1) * self.frame_size < len(self.injected_audio):
                    frame = self.injected_audio[self.injected_audio_index * self.frame_size : (self.injected_audio_index + 1) * self.frame_size]
                    self.injected_audio_index += 1
                    return frame
                else:
                    self.injected_audio = None
                    return None
            else:
                return None

    async def inject_audio(self, audio_data):
        async with self.lock:
            total_length = len(audio_data)
            if total_length % self.frame_size != 0:
                raise ValueError("Injected audio is not a multiple of frame size")

            self.injected_audio = audio_data
            self.injected_audio_index = 0

@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)
    output_audio_streams[sid] = OutputAudioStream()
    audio_agents[sid] = AudioAgent(output_audio_streams[sid])
    sio.start_background_task(send_audio_to_client, sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)
    del output_audio_streams[sid]
    del audio_agents[sid]

@sio.event
async def audio_input(sid, data):
    audio_data = np.frombuffer(data, dtype=np.float32)
    await audio_agents[sid].process_input_audio(audio_data)

async def send_audio_to_client(sid):
    while sid in output_audio_streams:
        try:
            audio_frame = await output_audio_streams[sid].get_audio_frame()
            if audio_frame is not None:
                await sio.emit('audio', audio_frame.tolist(), room=sid)
            else:
                await asyncio.sleep(0.01)
        except KeyError:
            pass

app.router.add_get('/', lambda request: web.Response(text="WebSocket Audio Server"))

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
