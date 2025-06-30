import google.generativeai as genai
import os
from typing import AsyncGenerator

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_response(messages: list[dict]) -> str:
    formatted_history = [
        {"role": m["role"], "parts": [m["content"]]}
        for m in messages if m["role"] in {"user", "assistant"}
    ]

    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat(history=formatted_history[:-1])

    prompt = messages[-1]["content"]
    response = chat.send_message(prompt)

    return response.text

def format_messages(messages: list[dict]) -> str:
    formatted_messages = []
    for msg in messages:
        if msg["role"] == "user":
            formatted_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg["role"] == "assistant":
            formatted_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

    return formatted_messages