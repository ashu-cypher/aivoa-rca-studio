"""Groq integration config tests — no live key needed, no key values asserted."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import Settings


def test_settings_loads_from_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=test-key-from-env-file\nGROQ_MODEL=test-model-x\n")
    s = Settings(_env_file=str(env_file))
    assert s.groq_api_key == "test-key-from-env-file"
    assert s.groq_model == "test-model-x"


def test_missing_key_check_reports_not_configured(monkeypatch):
    from app.services import llm

    monkeypatch.setattr("app.services.llm.settings.groq_api_key", None)
    check = llm.check_model_available()
    assert check["configured"] is False
    assert check["model_available"] is None
