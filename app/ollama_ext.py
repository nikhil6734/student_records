"""Optional extension: answer natural-language questions about stored students via a local Ollama server."""
import json
import os
import urllib.error
import urllib.request

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


class OllamaUnavailable(Exception):
    pass


def ask_about_students(question: str, records: list[dict]) -> str:
    prompt = (
        "You answer questions about student records. Use only the data below.\n\n"
        f"Records (JSON):\n{json.dumps(records, default=str)}\n\n"
        f"Question: {question}\nAnswer:"
    )
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OllamaUnavailable(str(exc)) from exc
    return body.get("response", "").strip()
