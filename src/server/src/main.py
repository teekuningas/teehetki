import asyncio
import numpy as np
import aiohttp_cors
from aiohttp import web
import socketio
import datetime

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

class AudioAgent:
    def __init__(self, output_audio_stream):
        self.output_audio_stream = output_audio_stream

        self.input_buffer = np.array([], dtype=np.float32)

        self.beginning = datetime.datetime.now()
        self.injection_flag = False

    async def process_input_audio(self, audio_data):
        if not self.injection_flag:
            self.input_buffer = np.concatenate([self.input_buffer, audio_data])

        elapsed = datetime.datetime.now() - self.beginning

        if elapsed > datetime.timedelta(seconds=10):
            if not self.injection_flag:
                self.injection_flag = True
                await self.inject_sine_waves()

    async def inject_sine_waves(self):
        # Test playing some sine waves
        sample_rate = self.output_audio_stream.sample_rate
        wave = generate_sine_wave(440, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = generate_sine_wave(550, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = generate_sine_wave(660, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = generate_sine_wave(770, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = generate_sine_wave(880, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)

        # And repeating input to output
        input_wave = np.array(self.input_buffer)
        input_wave = np.nan_to_num(input_wave, nan=0.0)
        frame_size = self.output_audio_stream.frame_size
        padding_needed = (frame_size - (len(input_wave) % frame_size)) % frame_size
        padded_wave = np.pad(input_wave, (0, padding_needed), mode='constant', constant_values=0)
        await self.output_audio_stream.inject_audio(padded_wave)

output_audio_streams = {}
audio_agents = {}

def generate_sine_wave(frequency, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return wave

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
