import aiohttp
import asyncio
import os


async def llm(chat_history):
    """A simple function that calls llm api to get a chat-like response given the input text."""
    base_url = os.getenv("API_ADDRESS", "http://localhost:8080")
    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    # Get API key from env variable
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        headers["Authorization"] = f"Bearer {openai_api_key}"

    # Get organization from env variable
    openai_org_id = os.getenv("OPENAI_ORGANIZATION")
    if openai_org_id:
        headers["OpenAI-Organization"] = openai_org_id

    # Get LLM model from env variable
    model = os.getenv("LLM_MODEL", "gpt-4")

    # Get temperature from env variable
    try:
        temperature = float(os.getenv("LLM_TEMPERATURE", 0.7))
    except ValueError:
        temperature = 0.7

    messages = [
        {
            "role": "system",
            "content": "Vastaa käyttäjälle aina hyvin lyhyesti, korkeintaan kymmenellä sanalla.",
        },
    ]

    messages.extend(chat_history)

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 70,
        "temperature": temperature,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            response_json = await response.json()
            return response_json["choices"][0]["message"]["content"]
