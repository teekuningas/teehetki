import aiohttp
import asyncio
import numpy as np
import io
from scipy.io.wavfile import read
import librosa


async def tts(text, sample_rate):
    """A simple function that uses api to generate speech from text."""
    url = "http://localhost:8080/tts"
    headers = {"Content-Type": "application/json"}
    payload = {"input": text, "model": "tts-1"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            audio_data = await response.read()

            # Load the audio data from the response
            with io.BytesIO(audio_data) as f:
                original_sr, data = read(f)

            # Ensure the data is in float32 format
            if data.dtype != np.float32:
                data = data.astype(np.float32) / np.iinfo(data.dtype).max

            # Downsample the audio if needed
            if original_sr != sample_rate:
                data = librosa.resample(
                    data, orig_sr=original_sr, target_sr=sample_rate
                )

            return data
