import aiohttp
import asyncio


async def llm(text):
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "Vastaa käyttäjälle hyvin lyhyesti, korkeintaan kymmenellä sanalla.",
            },
            {"role": "user", "content": text},
        ],
        "max_tokens": 70,
        "temperature": 0.7,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            response_json = await response.json()
            return response_json["choices"][0]["message"]["content"]
