import aiohttp
import asyncio
import numpy as np
import io
from pydub import AudioSegment
import librosa
import os


async def tts(text, sample_rate):
    """A simple function that uses api to generate speech from text."""
    base_url = os.getenv("API_ADDRESS", "http://localhost:8080")
    url = f"{base_url}/v1/audio/speech"
    headers = {"Content-Type": "application/json"}

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        headers["Authorization"] = f"Bearer {openai_api_key}"

    openai_org_id = os.getenv("OPENAI_ORGANIZATION")
    if openai_org_id:
        headers["OpenAI-Organization"] = openai_org_id

    payload = {
        "input": text,
        "model": "tts-1",
        "response_format": "wav",
        "voice": "alloy",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            audio_data = await response.read()

            # Load the audio data from the response using pydub
            with io.BytesIO(audio_data) as f:
                audio = AudioSegment.from_file(f, format="wav")

            # Convert AudioSegment to numpy array
            data = np.array(audio.get_array_of_samples(), dtype=np.float32)

            # Normalize the data to the range [-1.0, 1.0]
            data /= np.iinfo(audio.array_type).max

            # Downsample the audio if needed
            if audio.frame_rate != sample_rate:
                data = librosa.resample(
                    data, orig_sr=audio.frame_rate, target_sr=sample_rate
                )

            return data
