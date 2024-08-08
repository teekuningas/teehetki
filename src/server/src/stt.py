import numpy as np
import aiohttp
import aiofiles
import io
from scipy.io.wavfile import write
import librosa
import asyncio

dest_sample_rate = 16000


async def stt(audio_data, sample_rate, language="fi"):
    if sample_rate != dest_sample_rate:
        audio_data = librosa.resample(
            audio_data, orig_sr=sample_rate, target_sr=dest_sample_rate
        )

    with io.BytesIO() as wav_buffer:
        write(wav_buffer, dest_sample_rate, audio_data)
        wav_buffer.seek(0)

        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field(
                "file", wav_buffer, filename="audio.wav", content_type="audio/wav"
            )
            form_data.add_field("model", "whisper-1")
            form_data.add_field("language", language)

            async with session.post(
                "http://localhost:8080/v1/audio/transcriptions", data=form_data
            ) as response:
                response_json = await response.json()
                return response_json["text"]
