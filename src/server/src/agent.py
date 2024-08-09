import aiohttp
import asyncio

from vad import VAD
from stt import stt
from llm import llm
from tts import tts


class AudioAgent:
    """A class representing an audio processing agent that uses VAD, STT, LLM, and TTS."""

    def __init__(self, sid, output_audio_stream):
        self.sid = sid
        self.output_audio_stream = output_audio_stream
        self.sample_rate = output_audio_stream.sample_rate
        self.frame_size = output_audio_stream.frame_size

        self.vad = VAD(sample_rate=self.sample_rate)
        self.is_processing = False

        self.chat_history = []

    async def get_status(self):
        return {
            "is_processing": self.is_processing,
            "chat_history": self.chat_history,
        }

    async def update_settings(self, settings):
        threshold = settings["threshold"]
        self.vad.update_threshold(threshold)

    async def process_input_audio(self, audio_data):
        if self.is_processing:
            return

        result = self.vad.detect(audio_data)

        if result["detected"]:

            # Disallow new recordings
            self.is_processing = True

            # Get audio segment from VAD
            segment = result["segment"]
            print(f"{self.sid}: Detected a speech segment of length {len(segment)}!")

            try:
                # Use speech-to-text to get a textual representation
                input_text = await stt(segment, self.sample_rate)
                print(f"{self.sid}: Input was: {input_text}")

                self.chat_history.append({"role": "user", "content": input_text})

                # Use llm to get a chat-like response to the textual input
                output_text = await llm(self.chat_history)
                print(f"{self.sid}: Output was: {output_text}")

                self.chat_history.append({"role": "assistant", "content": output_text})

                # Use text-to-speech to get audio output from the chat response
                output_audio_data = await tts(output_text, self.sample_rate)

                # Inject it into the output stream
                await self.output_audio_stream.inject_audio(output_audio_data)

                # Wait approximately as long as the audio would play before
                # allowing new recordings
                await asyncio.sleep((len(output_audio_data) / self.sample_rate) + 1)
            except aiohttp.client_exceptions.ClientOSError:
                print("Cannot connect to the api server.")

            # Allow new recordings
            self.is_processing = False
