import sys
import types

import pytest


def run_cli(argv, monkeypatch, expectations):
    """Helper to run src.cli.main() with patched write_config and get_config_summary.

    expectations: dict with keys to assert on write_config kwargs.
    """
    # Ensure a clean import each time by removing from sys.modules
    sys.modules.pop('src.cli', None)

    calls = {"write_config": None, "printed": []}

    def fake_write_config(**kwargs):
        calls["write_config"] = kwargs
        return "/tmp/fake-config.json"

    def fake_get_config_summary():
        return "provider=none"

    def fake_print(*args, **kwargs):
        calls["printed"].append(" ".join(str(a) for a in args))

    import importlib
    cli = importlib.import_module('src.cli')

    # Patch targets in src.cli namespace (write_config/get_config_summary/print)
    monkeypatch.setattr(cli, 'write_config', fake_write_config)
    monkeypatch.setattr(cli, 'get_config_summary', fake_get_config_summary)
    monkeypatch.setattr(cli, 'run_config_menu', lambda non_interactive=False: (_ for _ in ()).throw(AssertionError("run_config_menu should not be called in these tests")))
    monkeypatch.setattr(cli, 'print', fake_print, raising=False)

    old_argv = sys.argv
    try:
        sys.argv = ["semfire", *argv]
        cli.main()
    finally:
        sys.argv = old_argv

    # Verify expectations on write_config when provided
    if expectations is not None:
        assert calls["write_config"] is not None, "write_config should have been called"
        for k, v in expectations.items():
            assert calls["write_config"].get(k) == v, f"Expected {k}={v}, got {calls['write_config'].get(k)}"
    else:
        # No write expected; ensure summary printed
        assert any("provider=none" in line for line in calls["printed"])  # non-interactive summary path


def test_config_gemini_flags(monkeypatch):
    run_cli(
        [
            "config",
            "--provider", "gemini",
            "--gemini-model", "gem-1.5",
            "--gemini-api-key-env", "GEMINI_API_KEY",
            "--non-interactive",
        ],
        monkeypatch,
        expectations={
            "provider": "gemini",
            "gemini_model": "gem-1.5",
            "gemini_api_key_env": "GEMINI_API_KEY",
        },
    )


def test_config_openrouter_flags(monkeypatch):
    run_cli(
        [
            "config",
            "--provider", "openrouter",
            "--openrouter-model", "deepseek/deepseek-chat",
            "--openrouter-api-key-env", "OPENROUTER_API_KEY",
        ],
        monkeypatch,
        expectations={
            "provider": "openrouter",
            "openrouter_model": "deepseek/deepseek-chat",
            "openrouter_api_key_env": "OPENROUTER_API_KEY",
        },
    )


def test_config_perplexity_flags(monkeypatch):
    run_cli(
        [
            "config",
            "--provider", "perplexity",
            "--perplexity-model", "sonar-medium-online",
            "--perplexity-api-key-env", "PERPLEXITY_API_KEY",
        ],
        monkeypatch,
        expectations={
            "provider": "perplexity",
            "perplexity_model": "sonar-medium-online",
            "perplexity_api_key_env": "PERPLEXITY_API_KEY",
        },
    )


def test_config_non_interactive_summary_only(monkeypatch):
    # No flags -> should not call write_config; should print summary in non-interactive mode
    run_cli(
        [
            "config",
            "--non-interactive",
        ],
        monkeypatch,
        expectations=None,
    )

