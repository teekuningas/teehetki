import numpy as np
import datetime
import asyncio

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
        wave = self.generate_sine_wave(440, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = self.generate_sine_wave(550, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = self.generate_sine_wave(660, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = self.generate_sine_wave(770, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)
        wave = self.generate_sine_wave(880, 1, sample_rate)
        await self.output_audio_stream.inject_audio(wave)
        await asyncio.sleep(1)

        # And repeating input to output
        input_wave = np.array(self.input_buffer)
        input_wave = np.nan_to_num(input_wave, nan=0.0)
        frame_size = self.output_audio_stream.frame_size
        padding_needed = (frame_size - (len(input_wave) % frame_size)) % frame_size
        padded_wave = np.pad(input_wave, (0, padding_needed), mode='constant', constant_values=0)
        await self.output_audio_stream.inject_audio(padded_wave)

    def generate_sine_wave(self, frequency, duration, sample_rate):
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        wave = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        return wave
