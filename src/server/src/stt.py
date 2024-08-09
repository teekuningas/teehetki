import numpy as np
import aiohttp
import io
from scipy.io.wavfile import write
import librosa
import asyncio
import os

dest_sample_rate = 16000


async def stt(audio_data, sample_rate, language="fi"):
    """A simple function that uses api to get textual representation from speech."""
    if sample_rate != dest_sample_rate:
        audio_data = librosa.resample(
            audio_data, orig_sr=sample_rate, target_sr=dest_sample_rate
        )

    with io.BytesIO() as wav_buffer:
        write(wav_buffer, dest_sample_rate, audio_data)
        wav_buffer.seek(0)

        base_url = os.getenv("API_ADDRESS", "http://localhost:8080")
        url = f"{base_url}/v1/audio/transcriptions"
        headers = {}

        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_org_id = os.getenv("OPENAI_ORGANIZATION")

        if openai_api_key:
            headers["Authorization"] = f"Bearer {openai_api_key}"
        if openai_org_id:
            headers["OpenAI-Organization"] = openai_org_id

        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field(
                "file", wav_buffer, filename="audio.wav", content_type="audio/wav"
            )
            form_data.add_field("model", "whisper-1")
            form_data.add_field("language", language)

            async with session.post(url, headers=headers, data=form_data) as response:
                response_json = await response.json()
                return response_json["text"]
