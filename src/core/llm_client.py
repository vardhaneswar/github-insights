# src/core/llm_client.py
import os
import json
import requests

HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY is not set in environment variables.")

MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"

def generate_answer_from_llm(messages):

    url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.2,
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        raise RuntimeError(f"HF API Error: {response.text}")

    data = response.json()

    return data["choices"][0]["message"]["content"]
