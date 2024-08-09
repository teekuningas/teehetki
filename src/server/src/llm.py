import aiohttp
import asyncio
import os


async def llm(text):
    """A simple function that calls llm api to get a chat-like response given the input text."""
    base_url = os.getenv("API_ADDRESS", "http://localhost:8080")
    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        headers["Authorization"] = f"Bearer {openai_api_key}"

    openai_org_id = os.getenv("OPENAI_ORGANIZATION")
    if openai_org_id:
        headers["OpenAI-Organization"] = openai_org_id

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
