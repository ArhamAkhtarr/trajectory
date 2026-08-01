import json
import logging
import os
import re
import httpx

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


def clean_json_string(text: str) -> str:
    """Extracts JSON substring (objects or arrays) from markdown code fences or raw LLM text output."""
    if not text:
        return ""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()

    arr_start = text.find("[")
    arr_end = text.rfind("]")
    obj_start = text.find("{")
    obj_end = text.rfind("}")

    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        if obj_start == -1 or arr_start < obj_start:
            return text[arr_start:arr_end+1]

    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        return text[obj_start:obj_end+1]

    return text.strip()


async def query_ollama(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    json_format: bool = False,
    timeout: float = 90.0,
) -> str:
    """Queries Groq Cloud API (if GROQ_API_KEY is present) or local Ollama instance running Qwen2.5 3B."""
    groq_api_key = os.getenv("GROQ_API_KEY")

    if groq_api_key and groq_api_key.strip():
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key.strip()}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": groq_model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_format:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content
                else:
                    logger.error(f"Groq API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to query Groq API: {e}")

    # Fallback to local Ollama instance
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt
    if json_format:
        payload["format"] = "json"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"Ollama returned status {response.status_code}: {response.text}")
                return ""
    except Exception as e:
        logger.error(f"Failed to query Ollama at {OLLAMA_HOST} for model '{OLLAMA_MODEL}': {e}")
        return ""
