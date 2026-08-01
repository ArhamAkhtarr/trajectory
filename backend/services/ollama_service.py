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
    """Queries local Ollama instance running Qwen2.5 3B."""
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
