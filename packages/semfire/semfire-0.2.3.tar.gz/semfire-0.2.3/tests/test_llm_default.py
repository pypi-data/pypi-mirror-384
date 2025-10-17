import os
import json
import sys
import importlib


def test_llm_default_openai_mock(monkeypatch, tmp_path):
    # Configure provider via file and env indirection
    cfg_path = tmp_path / "config.json"
    cfg = {
        "provider": "openai",
        "openai": {
            "model": "gpt-4o-mini",
            "api_key_env": "TEST_OPENAI_KEY",
            "base_url": None,
        }
    }
    cfg_path.write_text(json.dumps(cfg))
    monkeypatch.setenv("SEMFIRE_CONFIG", str(cfg_path))
    monkeypatch.setenv("TEST_OPENAI_KEY", "sk-test-123")

    # Mock openai.ChatCompletion.create
    class MockChatCompletion:
        @staticmethod
        def create(model, messages, temperature, max_tokens):
            return {
                "choices": [
                    {"message": {"content": "LLM_RESPONSE_MARKER: Mocked analysis OK."}}
                ]
            }

    class MockOpenAI:
        ChatCompletion = MockChatCompletion
        api_key = None
        api_base = None

    # Install mock module under name 'openai'
    import types
    mock_mod = types.ModuleType("openai")
    mock_mod.ChatCompletion = MockChatCompletion
    mock_mod.api_key = None
    mock_mod.api_base = None
    monkeypatch.setitem(sys.modules, "openai", mock_mod)

    from src.detectors import EchoChamberDetector

    detector = EchoChamberDetector()
    res = detector.analyze_text("This is a test.")
    assert res["llm_status"] == "llm_analysis_success"
    assert "LLM_RESPONSE_MARKER: " in res["llm_analysis"]


def test_llm_default_none(monkeypatch, tmp_path):
    # Provider explicitly none
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"provider": "none"}))
    monkeypatch.setenv("SEMFIRE_CONFIG", str(cfg_path))

    from src.detectors import EchoChamberDetector
    detector = EchoChamberDetector()
    res = detector.analyze_text("Hello")
    assert res["llm_status"] in ("llm_model_not_loaded", "llm_analysis_error")
