import json
import os
import sys
import subprocess


def run_cli(args, env=None):
    cmd = [sys.executable, "-m", "src.cli"] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def test_semfire_config_cli_openai(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    env = os.environ.copy()
    env["SEMFIRE_CONFIG"] = str(cfg_path)
    # Use a dummy env var indirection for API key, not the real one
    env["TEST_OPENAI_KEY"] = "sk-test-123"

    rc, out, err = run_cli([
        "config",
        "--provider", "openai",
        "--openai-model", "gpt-4o-mini",
        "--openai-api-key-env", "TEST_OPENAI_KEY",
    ], env=env)
    assert rc == 0, err
    assert str(cfg_path) in out
    assert "provider=openai" in out

    # Verify file contents
    data = json.loads(cfg_path.read_text())
    assert data["provider"] == "openai"
    assert data["openai"]["api_key_env"] == "TEST_OPENAI_KEY"
    assert data["openai"]["model"] == "gpt-4o-mini"


