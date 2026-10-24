"""Groq LLM client. Keys live only on the backend, via env vars.

No fallback fabrication: if the key is missing or the provider fails after
retries, raise ProviderError so the API returns a clear 503/502, never fake AI output.
"""

import json
import time

import httpx

from app.core.config import settings


class ProviderError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def complete_json(system: str, user: str, *, timeout: float = 60.0) -> dict:
    """Call Groq chat completions with JSON-object mode; return parsed dict."""
    if not settings.groq_api_key:
        raise ProviderError(
            "GROQ_API_KEY is not configured on the backend. Set it in backend/.env and restart the backend, then retry.",
            status=503,
        )
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.groq_model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"},
                    },
                )
            if resp.status_code == 429:
                raise ProviderError("Groq rate limit reached. Wait a minute and retry.", status=502)
            if resp.status_code >= 400:
                # Do not leak raw provider body/secrets to ordinary users.
                raise ProviderError(f"Groq provider returned HTTP {resp.status_code}. Check the configured model and key, then retry.", status=502)
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ProviderError("Groq returned a non-object response. Retry.", status=502)
            return parsed
        except ProviderError:
            raise
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            last_err = e
            time.sleep(0.5)
    raise ProviderError(f"AI provider request failed after retries ({last_err}). Please retry.", status=502)
