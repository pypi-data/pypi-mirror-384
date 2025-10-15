import os

import pytest

from nocturnal_archive.setup_config import KEY_PLACEHOLDER, NocturnalConfig


@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    yield


def test_import_secrets_prefers_keyring(monkeypatch):
    config = NocturnalConfig()
    monkeypatch.setattr(config, "_store_secret", lambda name, value: True)

    result = config.import_secrets({
        "GROQ_API_KEY": "gsk_real",
        "OPENALEX_API_KEY": "openalex-key",
    })

    stored = config.load_config()
    assert stored["GROQ_API_KEY"] == KEY_PLACEHOLDER
    assert stored["OPENALEX_API_KEY"] == KEY_PLACEHOLDER
    assert result["GROQ_API_KEY"] == (True, "stored in keyring")
    assert result["OPENALEX_API_KEY"] == (True, "stored in keyring")


def test_import_secrets_falls_back_to_plaintext(monkeypatch):
    config = NocturnalConfig()
    monkeypatch.setattr(config, "_store_secret", lambda name, value: False)

    result = config.import_secrets({
        "OPENALEX_API_KEY": "openalex-key",
    })

    stored = config.load_config()
    assert stored["OPENALEX_API_KEY"] == "openalex-key"
    assert result["OPENALEX_API_KEY"] == (True, "stored in config file")


def test_import_secrets_respects_plaintext_opt_out(monkeypatch):
    config = NocturnalConfig()
    monkeypatch.setattr(config, "_store_secret", lambda name, value: False)

    result = config.import_secrets({
        "PUBMED_API_KEY": "pubmed-key",
    }, allow_plaintext=False)

    stored = config.load_config()
    assert "PUBMED_API_KEY" not in stored
    assert result["PUBMED_API_KEY"] == (False, "keyring unavailable and plaintext disabled")

