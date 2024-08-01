import asyncio
import socketio
from aiohttp import web
import numpy as np
from collections import deque

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])
app = web.Application()
sio.attach(app)

class OutputAudioStream:
    def __init__(self):
        print("Initializing output audio stream")
        self.sample_rate = 48000
        self.frame_duration = 0.02  # 20ms
        self.frame_size = int(self.sample_rate * self.frame_duration)
        self.silence = np.zeros(self.frame_size, dtype=np.float32)  # 20ms of silence
        self.buffer = deque([self.silence] * (self.sample_rate // self.frame_size))

    def get_audio_frame(self):
        if not self.buffer:
            self.buffer.extend([self.silence] * (self.sample_rate // self.frame_size))
        frame = self.buffer.popleft()
        return frame

    def inject_audio(self, audio_data):
        num_frames = len(audio_data) // self.frame_size
        audio_frames = np.split(audio_data[:num_frames * self.frame_size], num_frames)
        for frame in audio_frames:
            self.buffer.append(frame)
            if len(self.buffer) > (self.sample_rate // self.frame_size):
                self.buffer.popleft()

# output_audio_stream = OutputAudioStream()
# This should be run in a loop
# output_audio_stream.inject_audio(audio_data)
# sio.start_background_task(send_audio_to_client, sid)

async def audio_injector():
    while True:
        await asyncio.sleep(5)
        sine_wave = generate_sine_wave(440, 2)  # 440 Hz for 2 seconds
        print('Injecting sine wave:', sine_wave) # Debug
        output_audio_stream.inject_audio(sine_wave)

def generate_sine_wave(frequency, duration, sample_rate=48000):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)

@sio.event
async def connect(sid, environ):
    print('Client connected:', sid) # Debug

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid) # Debug

@sio.event
async def audio(sid, data):
    audio_data = np.array(data, dtype=np.float32)
    print('Received audio data from client:', audio_data) # Debug

async def send_audio_to_client(sid):
    while True:
        await asyncio.sleep(0.02) # 20ms
        audio_frame = output_audio_stream.get_audio_frame()
        print('Sending audio data to client:', audio_frame) # Debug
        await sio.emit('audio', audio_frame.tolist(), room=sid)

app.router.add_get('/', lambda request: web.Response(text="WebSocket Audio Server"))

if __name__ == '__main__':
    web.run_app(app, port=5000)
