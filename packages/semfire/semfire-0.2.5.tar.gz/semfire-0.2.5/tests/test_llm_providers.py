import pytest
import os
import json
from unittest.mock import MagicMock, patch

from src.detectors.llm_provider import (
    OpenAIProvider,
    GeminiProvider,
    OpenRouterProvider,
    PerplexityProvider,
    load_llm_provider_from_config,
    _read_config,
    _load_env_file_into_process,
    write_config,
    get_config_summary,
    DEFAULT_CONFIG_PATH,
    CONFIG_ENV
)

# Helper to clean up config file after tests
@pytest.fixture(autouse=True)
def cleanup_config_file():
    config_path = os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)
    if os.path.exists(config_path):
        os.remove(config_path)
    yield
    if os.path.exists(config_path):
        os.remove(config_path)


# Mock response for requests.post for Gemini, OpenRouter, Perplexity
class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


# --- Test Gemini Provider ---

def test_gemini_generate_success(monkeypatch):
    mock_api_key = "test_gemini_key"
    mock_model = "gemini-pro"
    os.environ["GEMINI_API_KEY"] = mock_api_key

    # Mock requests.post
    def mock_post(*args, **kwargs):
        assert mock_api_key in args[0] # Ensure API key is in URL
        return MockResponse({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Gemini generated text."
                    }]
                }
            }]
        })

    monkeypatch.setattr("requests.post", mock_post)

    provider = GeminiProvider(model=mock_model, api_key=mock_api_key)
    assert provider.is_ready()
    result = provider.generate("test prompt")
    assert result == "Gemini generated text."


# --- Test OpenRouter Provider ---

def test_openrouter_generate_success(monkeypatch):
    mock_api_key = "test_openrouter_key"
    mock_model = "deepseek/deepseek-chat"
    os.environ["OPENROUTER_API_KEY"] = mock_api_key

    # Mock requests.post
    def mock_post(*args, **kwargs):
        assert kwargs["headers"]["Authorization"] == f"Bearer {mock_api_key}"
        return MockResponse({
            "choices": [{
                "message": {
                    "content": "OpenRouter generated text."
                }
            }]
        })

    monkeypatch.setattr("requests.post", mock_post)

    provider = OpenRouterProvider(model=mock_model, api_key=mock_api_key)
    assert provider.is_ready()
    result = provider.generate("test prompt")
    assert result == "OpenRouter generated text."


# --- Test Perplexity Provider ---

def test_perplexity_generate_success(monkeypatch):
    mock_api_key = "test_perplexity_key"
    mock_model = "sonar-medium-online"
    os.environ["PERPLEXITY_API_KEY"] = mock_api_key

    # Mock requests.post
    def mock_post(*args, **kwargs):
        assert kwargs["headers"]["Authorization"] == f"Bearer {mock_api_key}"
        return MockResponse({
            "choices": [{
                "message": {
                    "content": "Perplexity generated text."
                }
            }]
        })

    monkeypatch.setattr("requests.post", mock_post)

    provider = PerplexityProvider(model=mock_model, api_key=mock_api_key)
    assert provider.is_ready()
    result = provider.generate("test prompt")
    assert result == "Perplexity generated text."


# --- Test Auto-detect Precedence ---

def test_auto_detect_order(monkeypatch):
    # Mock _load_env_file_into_process to prevent loading from .env files during this test
    monkeypatch.setattr("src.detectors.llm_provider._load_env_file_into_process", lambda: None)

    # Clear all relevant env vars first
    for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "PERPLEXITY_API_KEY", "SEMFIRE_LLM_PROVIDER"]:
        if key in os.environ:
            del os.environ[key]

    # Test OpenAI precedence
    os.environ["OPENAI_API_KEY"] = "openai_key"
    os.environ["GEMINI_API_KEY"] = "gemini_key" # Should be ignored due to OpenAI precedence
    provider = load_llm_provider_from_config()
    assert isinstance(provider, OpenAIProvider)
    del os.environ["OPENAI_API_KEY"]
    del os.environ["GEMINI_API_KEY"] # Clean up for next test

    # Test Gemini precedence
    os.environ["GEMINI_API_KEY"] = "gemini_key"
    os.environ["OPENROUTER_API_KEY"] = "openrouter_key" # Should be ignored
    provider = load_llm_provider_from_config()
    assert isinstance(provider, GeminiProvider)
    del os.environ["GEMINI_API_KEY"]
    del os.environ["OPENROUTER_API_KEY"]

    # Test OpenRouter precedence
    os.environ["OPENROUTER_API_KEY"] = "openrouter_key"
    os.environ["PERPLEXITY_API_KEY"] = "perplexity_key" # Should be ignored
    provider = load_llm_provider_from_config()
    assert isinstance(provider, OpenRouterProvider)
    del os.environ["OPENROUTER_API_KEY"]
    del os.environ["PERPLEXITY_API_KEY"]

    # Test Perplexity precedence
    os.environ["PERPLEXITY_API_KEY"] = "perplexity_key"
    provider = load_llm_provider_from_config()
    assert isinstance(provider, PerplexityProvider)
    del os.environ["PERPLEXITY_API_KEY"]

    # Test no provider
    provider = load_llm_provider_from_config()
    assert provider is None


# --- Test write_config and get_config_summary ---

def test_write_config_and_summary(monkeypatch):
    config_path = os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)
    # Ensure config file doesn't exist before test
    if os.path.exists(config_path):
        os.remove(config_path)

    # Test OpenAI
    write_config("openai", openai_model="test-gpt", openai_api_key_env="MY_OPENAI_KEY")
    summary = get_config_summary()
    assert "provider=openai" in summary
    assert "model=test-gpt" in summary
    assert "api_key_env=MY_OPENAI_KEY" in summary
    cfg = _read_config()
    assert cfg["provider"] == "openai"
    assert cfg["openai"]["model"] == "test-gpt"
    assert cfg["openai"]["api_key_env"] == "MY_OPENAI_KEY"
    os.remove(config_path)

    # Test Gemini
    write_config("gemini", gemini_model="test-gemini", gemini_api_key_env="MY_GEMINI_KEY")
    summary = get_config_summary()
    assert "provider=gemini" in summary
    assert "model=test-gemini" in summary
    assert "api_key_env=MY_GEMINI_KEY" in summary
    cfg = _read_config()
    assert cfg["provider"] == "gemini"
    assert cfg["gemini"]["model"] == "test-gemini"
    assert cfg["gemini"]["api_key_env"] == "MY_GEMINI_KEY"
    os.remove(config_path)

    # Test OpenRouter
    write_config("openrouter", openrouter_model="test-openrouter", openrouter_api_key_env="MY_OPENROUTER_KEY")
    summary = get_config_summary()
    assert "provider=openrouter" in summary
    assert "model=test-openrouter" in summary
    assert "api_key_env=MY_OPENROUTER_KEY" in summary
    cfg = _read_config()
    assert cfg["provider"] == "openrouter"
    assert cfg["openrouter"]["model"] == "test-openrouter"
    assert cfg["openrouter"]["api_key_env"] == "MY_OPENROUTER_KEY"
    os.remove(config_path)

    # Test Perplexity
    write_config("perplexity", perplexity_model="test-perplexity", perplexity_api_key_env="MY_PERPLEXITY_KEY")
    summary = get_config_summary()
    assert "provider=perplexity" in summary
    assert "model=test-perplexity" in summary
    assert "api_key_env=MY_PERPLEXITY_KEY" in summary
    cfg = _read_config()
    assert cfg["provider"] == "perplexity"
    assert cfg["perplexity"]["model"] == "test-perplexity"
    assert cfg["perplexity"]["api_key_env"] == "MY_PERPLEXITY_KEY"
    os.remove(config_path)

    # Test Transformers (config only, no API key)
    write_config("transformers") # Only provider name is needed for transformers
    cfg = _read_config()
    assert cfg["provider"] == "transformers"
    os.remove(config_path)

    # Test 'none' provider
    write_config("none")
    summary = get_config_summary()
    assert "provider=none" in summary
    cfg = _read_config()
    assert cfg["provider"] == "none"
    os.remove(config_path)
