import asyncio
import numpy as np
import aiohttp_cors
from aiohttp import web
import socketio
from agent import AudioAgent

sio = socketio.AsyncServer(
    async_mode="aiohttp", cors_allowed_origins=["http://localhost:3000"]
)
app = web.Application()
sio.attach(app)

# Hold on to streams and agents for each client
output_audio_streams = {}
audio_agents = {}


class OutputAudioStream:
    """This is a client-specific queue where the agent pushes data,
    and from which a background task polls data and sends it to the client socket.
    """

    def __init__(self):
        self.lock = asyncio.Lock()
        self.sample_rate = 8000
        self.frame_duration = 0.1
        self.frame_size = int(self.sample_rate * self.frame_duration)
        self.injected_audio = None
        self.current_frame_index = 0

    async def get_audio_frame(self):
        async with self.lock:
            if self.injected_audio is None:
                return None

            start = self.current_frame_index * self.frame_size
            end = start + self.frame_size

            if start < len(self.injected_audio):
                frame = self.injected_audio[start:end]
                self.current_frame_index += 1
                return frame

            self.injected_audio = None
            return None

    async def inject_audio(self, audio_data):
        async with self.lock:

            frame_size = self.frame_size
            padding_needed = (frame_size - len(audio_data) % frame_size) % frame_size
            padded_output = np.pad(
                audio_data,
                (0, padding_needed),
                mode="constant",
                constant_values=0,
            )
            self.injected_audio = padded_output
            self.current_frame_index = 0


@sio.event
async def connect(sid, environ):
    print(f"{sid}: Client connected.")

    # Create a stream for agent to inject into
    # and background socket task to pull from.
    output_audio_streams[sid] = OutputAudioStream()

    # Create a agent that listens to the input stream
    # and injects into the output stream.
    audio_agents[sid] = AudioAgent(sid, output_audio_streams[sid])

    # Start a task that will send available data to client.
    sio.start_background_task(send_audio_to_client, sid)

    # Start background task that send agent status to client.
    sio.start_background_task(send_agent_status_to_client, sid)


@sio.event
async def disconnect(sid):
    print(f"{sid}: Client disconnected.")
    del output_audio_streams[sid]
    del audio_agents[sid]


@sio.event
async def audio_input(sid, data):
    """Audio comes in from the socket."""
    audio_data = np.frombuffer(data, dtype=np.float32)
    await audio_agents[sid].process_input_audio(audio_data)


@sio.event
async def threshold_update(sid, data):
    """Threshold setting comes in from the socket."""
    print(f"{sid}: Updated threshold to {data}")
    threshold = float(data)
    if sid in audio_agents:
        await audio_agents[sid].update_vad_threshold(threshold)


async def send_audio_to_client(sid):
    """Poll audio from the queue and send it to the socket."""
    while sid in output_audio_streams:
        try:
            audio_frame = await output_audio_streams[sid].get_audio_frame()
            if audio_frame is not None:
                await sio.emit("audio", audio_frame.tolist(), room=sid)
            else:
                await asyncio.sleep(0.01)
        except KeyError:
            pass


async def send_agent_status_to_client(sid):
    """Poll status from agent and sent it to the socket."""
    while sid in audio_agents:
        try:
            status = await audio_agents[sid].get_status()
            await sio.emit("agent_status", status, room=sid)
            await asyncio.sleep(0.5)
        except KeyError:
            pass


app.router.add_get("/", lambda request: web.Response(text="WebSocket Audio Server"))

cors = aiohttp_cors.setup(
    app,
    defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True, expose_headers="*", allow_headers="*"
        )
    },
)

for route in app.router.routes():
    if route.resource.canonical == "/":
        cors.add(route)

if __name__ == "__main__":
    web.run_app(app, port=5000)
