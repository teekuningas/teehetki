import numpy as np
import asyncio

from vad import VAD
from stt import stt
from llm import llm
from tts import tts


class AudioAgent:
    def __init__(self, sid, output_audio_stream):
        self.sid = sid
        self.output_audio_stream = output_audio_stream
        self.sample_rate = output_audio_stream.sample_rate
        self.frame_size = output_audio_stream.frame_size

        self.vad = VAD(sample_rate=self.sample_rate)

        self.processing_flag = False

    async def update_vad_threshold(self, threshold):
        self.vad.update_threshold(threshold)

    async def process_input_audio(self, audio_data):
        if self.processing_flag:
            return

        result = self.vad.detect(audio_data)

        if result["detected"]:

            # disallow new recordings
            self.processing_flag = True

            segment = result["segment"]

            print(f"{self.sid}: Detected a speech segment of length {len(segment)}!")

            input_text = await stt(segment, self.sample_rate)
            print(f"{self.sid}: Input was: {input_text}")

            output_text = await llm(input_text)
            print(f"{self.sid}: Output was: {output_text}")

            output_audio_data = await tts(output_text, self.sample_rate)

            frame_size = self.frame_size
            padding_needed = (
                frame_size - (len(output_audio_data) % frame_size)
            ) % frame_size
            padded_output = np.pad(
                output_audio_data,
                (0, padding_needed),
                mode="constant",
                constant_values=0,
            )
            await self.output_audio_stream.inject_audio(padded_output)
            await asyncio.sleep(len(padded_output) / self.sample_rate)

            # allow new recordings
            self.processing_flag = False
