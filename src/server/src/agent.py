import numpy as np
import asyncio

from vad import VAD


class AudioAgent:
    def __init__(self, sid, output_audio_stream):
        self.sid = sid
        self.output_audio_stream = output_audio_stream
        self.sample_rate = output_audio_stream.sample_rate
        self.frame_size = output_audio_stream.frame_size

        self.vad = VAD(sample_rate=self.sample_rate)

        self.injection_flag = False

    async def update_vad_threshold(self, threshold):
        self.vad.update_threshold(threshold)

    async def process_input_audio(self, audio_data):
        if self.injection_flag:
            return

        result = self.vad.detect(audio_data)

        if result['detected']:

            # disallow new recordings
            self.injection_flag = True

            segment = result['segment']

            print(f"{self.sid}: Detected a speech segment of length {len(segment)}!")

            # wait for one second before playing
            await asyncio.sleep(1)

            # inject the detected segment into the stream
            frame_size = self.frame_size
            padding_needed = (frame_size - (len(segment) % frame_size)) % frame_size
            padded_segment = np.pad(
                segment, (0, padding_needed), mode="constant", constant_values=0
            )
            await self.output_audio_stream.inject_audio(padded_segment)

            # wait for it playing
            await asyncio.sleep(len(segment) / self.sample_rate)

            # allow new recordings
            self.injection_flag = False
