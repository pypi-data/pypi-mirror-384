# Transformers Provider Documentation

This document details the integration of a new Transformers-based LLM provider into the system, enabling local model generation via the Hugging Face `transformers` library.

## Key Features

*   **Local Generation:** Loads tokenizer and model via `transformers` for local generation.
*   **Lazy Loading:** Models are lazy-loaded on the first `generate()` call to ensure fast startup times.
*   **Model Paths:** Supports Hugging Face model IDs or local file paths. When a local path is provided, `local_files_only` is used.
*   **Device Selection:** Honors `cpu` or `cuda` device specifications, falling back to `cpu` if CUDA is unavailable.
*   **Authentication:** No Hugging Face token is required for local paths. Hub, private, or gated models may require a token.
*   **Readiness Check:** The `is_ready()` method verifies the presence of necessary libraries and the `model_path` without forcing a heavy model load.

## Configuration

The Transformers provider can be configured via JSON, environment variables, or programmatically.

### JSON Configuration

```json
{
  "transformers": {
    "model_path": "...",
    "device": "cpu|cuda"
  }
}
```

### Environment Variables

*   `SEMFIRE_LLM_PROVIDER=transformers`
*   `SEMFIRE_TRANSFORMERS_MODEL_PATH=<your_model_path>`
*   `SEMFIRE_TRANSFORMERS_DEVICE=cpu|cuda`

### Programmatic Configuration

```python
from detectors.llm_provider import write_config

write_config(
    "transformers",
    transformers_model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    transformers_device="cpu"
)
```

### CLI Configuration

The `semfire config` command now supports `provider=transformers` with dedicated flags:

```bash
semfire config --provider transformers --transformers-model-path TinyLlama/TinyLlama-1.1B-Chat-v1.0 --transformers-device cpu
```

## `is_ready()` and `generate()` Methods

*   **`is_ready()`:** This method efficiently determines if the provider can attempt generation without incurring the overhead of loading the model.
*   **`generate()`:** This method handles the lazy-loading of the model and proceeds with text generation.

The `EchoChamberDetector` is designed to work seamlessly with this provider, as it instructs the LLM to prepend `LLM_RESPONSE_MARKER` to its outputs.

## Sandbox Write Fallback

If writing to `~/.semfire/config.json` fails (e.g., in a sandboxed environment), the system transparently falls back to writing to a workspace-local `./.semfire/config.json`. The `SEMFIRE_CONFIG` environment variable is then set to ensure consistent reads from the fallback location.

