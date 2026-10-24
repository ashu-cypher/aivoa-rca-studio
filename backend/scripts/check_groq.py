"""Groq integration smoke check. Run from backend/:  python scripts/check_groq.py

Reads GROQ_API_KEY / GROQ_MODEL from process env or backend/.env (via app settings),
lists Groq models, and sends one tiny JSON-mode chat request.
Prints only booleans / model names / error categories — never the key.
Exit 0 = a real Groq JSON response came back. Exit 1 = not configured or provider error.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.services import llm  # noqa: E402


def main() -> int:
    print(f"model configured: {settings.groq_model}")
    print(f"key configured: {bool(settings.groq_api_key)}")
    check = llm.check_model_available()
    print(f"model available: {check['model_available']}")
    if check["error"]:
        print(f"error: {check['error']}")
        return 1
    out = llm.complete_json(
        "You are a test assistant. Return ONLY valid JSON.",
        'Return {"ok": true} as JSON.',
    )
    print(f"chat JSON response: {out}")
    return 0 if out.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
