"""Groq LLM client. Keys live only on the backend, via env vars / backend/.env.

No fallback fabrication: if the key is missing or the provider fails after
retries, raise ProviderError so the API returns a clear 503/502, never fake AI output.
The key is never logged, returned to the frontend, or stored in the database.
"""

import json
import time

import httpx

from app.core.config import settings

GROQ_BASE = "https://api.groq.com/openai/v1"


def _client(timeout: float) -> httpx.Client:
    """httpx client that does not choke on bracketed IPv6 entries in NO_PROXY.

    httpx's default trust_env=True parses NO_PROXY, and entries like "[::1]"
    (present in this sandbox's environment) crash URL parsing with
    'Invalid port'. So: ignore env proxy parsing, but still honour an explicit
    HTTP(S)_PROXY if one is set, which is what external egress needs here.
    On a normal machine with no proxy set, this is a direct connection.
    """
    import os

    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    # trust_env=False also ignores SSL_CERT_FILE, which this sandbox's egress
    # proxy needs (its CA bundle). Pass it explicitly when present; otherwise
    # default verification stays on — never verify=False in production code.
    verify = os.getenv("SSL_CERT_FILE") or os.getenv("CURL_CA_BUNDLE") or True
    return httpx.Client(timeout=timeout, trust_env=False, proxy=proxy or None, verify=verify)


class ProviderError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def check_model_available(timeout: float = 15.0) -> dict:
    """Verify the configured key + model against Groq's model list.

    Returns {"configured": bool, "model": str, "model_available": bool | None, "error": str | None}.
    model_available is None when the key is missing or the list call itself fails
    for a non-auth reason — it never claims a model is available on a failed check.
    """
    if not settings.groq_api_key:
        return {"configured": False, "model": settings.groq_model, "model_available": None,
                "error": "GROQ_API_KEY is not configured. Set it in backend/.env and restart the backend."}
    try:
        with _client(timeout) as client:
            resp = client.get(f"{GROQ_BASE}/models",
                              headers={"Authorization": f"Bearer {settings.groq_api_key}"})
        if resp.status_code == 401:
            return {"configured": True, "model": settings.groq_model, "model_available": None,
                    "error": "Groq rejected the key (HTTP 401). Check GROQ_API_KEY in backend/.env."}
        if resp.status_code != 200:
            return {"configured": True, "model": settings.groq_model, "model_available": None,
                    "error": f"Groq models endpoint returned HTTP {resp.status_code}."}
        ids = {m.get("id") for m in resp.json().get("data", [])}
        available = settings.groq_model in ids
        return {"configured": True, "model": settings.groq_model, "model_available": available,
                "error": None if available else
                f"Model '{settings.groq_model}' was not found in this Groq account's model list. "
                "Set GROQ_MODEL in backend/.env to a model the account offers and restart."}
    except (httpx.TimeoutException, httpx.TransportError) as e:
        return {"configured": True, "model": settings.groq_model, "model_available": None,
                "error": f"Could not reach Groq to check the model ({e})."}


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
            with _client(timeout) as client:
                resp = client.post(
                    f"{GROQ_BASE}/chat/completions",
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
            if resp.status_code == 401:
                raise ProviderError("Groq rejected the API key (HTTP 401). Check GROQ_API_KEY in backend/.env, then restart and retry.", status=502)
            if resp.status_code == 404:
                raise ProviderError(f"Groq model '{settings.groq_model}' was not found (HTTP 404). Set GROQ_MODEL in backend/.env to a model your Groq account offers, restart, and retry.", status=502)
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
