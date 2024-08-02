import asyncio
import numpy as np
from collections import deque
import aiohttp_cors
from aiohttp import web
import socketio

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])
app = web.Application()
sio.attach(app)

class OutputAudioStream:
    def __init__(self):
        print("Initializing output audio stream")
        self.sample_rate = 8000
        self.frame_duration = 0.1
        self.frame_size = int(self.sample_rate * self.frame_duration)
        self.silence = np.zeros(self.frame_size, dtype=np.float32)  # 2 seconds of silence
        self.buffer = deque([self.silence] * (self.sample_rate // self.frame_size))
        self.lock = asyncio.Lock()

    async def get_audio_frame(self):
        async with self.lock:
            if not self.buffer:
                self.buffer.append(self.silence)
            frame = self.buffer.popleft()
        return frame

    async def inject_audio(self, audio_data):
        num_frames = len(audio_data) // self.frame_size
        audio_frames = np.split(audio_data[:num_frames * self.frame_size], num_frames)
        async with self.lock:
            for frame in audio_frames:
                self.buffer.append(frame)

output_audio_stream = OutputAudioStream()

def generate_sine_wave(frequency, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return wave

@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

    sio.start_background_task(send_audio_to_client, sid)
    sio.start_background_task(inject_sine_waves, sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

@sio.event
async def audio(sid, data):
    audio_data = np.array(data, dtype=np.float32)
    # print('Received audio data from client:', audio_data)

async def inject_sine_waves(sid):
    sample_rate = output_audio_stream.sample_rate
    await asyncio.sleep(1)
    while True:
        wave = generate_sine_wave(440, 5, sample_rate)
        await output_audio_stream.inject_audio(wave)
        await asyncio.sleep(7)

async def send_audio_to_client(sid):
    while True:
        await asyncio.sleep(output_audio_stream.frame_duration)
        audio_frame = await output_audio_stream.get_audio_frame()

        # print('Sending audio data to client:', audio_frame)
        await sio.emit('audio', audio_frame.tolist(), room=sid)

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
