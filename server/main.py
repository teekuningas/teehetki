import asyncio
import numpy as np
import aiohttp_cors
from aiohttp import web
import socketio

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])
app = web.Application()
sio.attach(app)

class OutputAudioStream:
    def __init__(self):
        print("Initializing output audio stream")

        self.lock = asyncio.Lock()

        self.sample_rate = 8000
        self.frame_duration = 0.1
        self.frame_size = int(self.sample_rate * self.frame_duration)

        self.n_frames = 100
        self.buffer_length = self.n_frames * self.frame_size
        self.silence = np.zeros(self.frame_size, dtype=np.float32)
        self.background_audio = np.tile(self.silence, self.n_frames)
        self.current_index = 0

        self.injected_audio = None
        self.injected_audio_index = 0

    async def get_audio_frame(self):
        async with self.lock:

            frame = np.copy(self.background_audio[self.current_index * self.frame_size : (self.current_index + 1) * self.frame_size])

            # Mix in the injected audio if it exists
            if self.injected_audio is not None:
                if (self.injected_audio_index + 1) * self.frame_size < len(self.injected_audio):
                    inject_frame = self.injected_audio[self.injected_audio_index * self.frame_size : (self.injected_audio_index + 1) * self.frame_size]
                    self.injected_audio_index += 1
                    frame += inject_frame
                else:
                    self.injected_audio = None

            self.current_index += 1
            if self.current_index >= self.n_frames:
                self.current_index = 0

        return frame

    async def inject_audio(self, audio_data):
        async with self.lock:
            total_length = len(audio_data)
            if total_length > self.buffer_length:
                raise ValueError("Injected audio is longer than the buffer length")
            if total_length % self.frame_size != 0:
                raise ValueError("Injected audio is not a multiple of frame size")

            self.injected_audio = audio_data
            self.injected_audio_index = 0

output_audio_streams = {}

def generate_sine_wave(frequency, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return wave

@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)
    output_audio_streams[sid] = OutputAudioStream()
    sio.start_background_task(send_audio_to_client, sid)
    sio.start_background_task(inject_sine_waves, sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)
    del output_audio_streams[sid]

@sio.event
async def audio(sid, data):
    audio_data = np.array(data, dtype=np.float32)

async def inject_sine_waves(sid):
    while sid in output_audio_streams:
        try:
            sample_rate = output_audio_streams[sid].sample_rate
            await asyncio.sleep(1)
            wave = generate_sine_wave(440, 1, sample_rate)
            await output_audio_streams[sid].inject_audio(wave)
            await asyncio.sleep(1)
            wave = generate_sine_wave(550, 1, sample_rate)
            await output_audio_streams[sid].inject_audio(wave)
            await asyncio.sleep(1)
            wave = generate_sine_wave(660, 1, sample_rate)
            await output_audio_streams[sid].inject_audio(wave)
            await asyncio.sleep(1)
            wave = generate_sine_wave(770, 1, sample_rate)
            await output_audio_streams[sid].inject_audio(wave)
            await asyncio.sleep(1)
            wave = generate_sine_wave(880, 1, sample_rate)
            await output_audio_streams[sid].inject_audio(wave)
            await asyncio.sleep(1)
        except KeyError:
            pass

async def send_audio_to_client(sid):
    while sid in output_audio_streams:
        try:
            await asyncio.sleep(output_audio_streams[sid].frame_duration)
            audio_frame = await output_audio_streams[sid].get_audio_frame()
            await sio.emit('audio', audio_frame.tolist(), room=sid)
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
