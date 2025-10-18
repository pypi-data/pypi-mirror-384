# SemFire FAQ

This document answers frequently asked questions about the SemFire project.

## How does SemFire use AI?

In its default configuration, SemFire uses AI (specifically, a Large Language Model) in its **`EchoChamberDetector`**. This detector analyzes conversation history and the current message to identify characteristics of an "echo chamber" attack, where a user might be trying to manipulate the AI by reinforcing certain ideas.

The system is designed to use an OpenAI model by default, specifically **`gpt-4o-mini`**.

The other detectors (`RuleBasedDetector`, `HeuristicDetector`, and `InjectionDetector`) are **not** AI-based and rely on predefined rules and heuristics.

## How does SemFire handle API keys?

SemFire is designed to handle API keys securely. It **does not** store raw API keys in its configuration files. Instead, it retrieves them from the environment.

Here is the order of priority for key retrieval:

1.  **Environment Variables**: The application primarily looks for an environment variable, which is `OPENAI_API_KEY` by default.
2.  **.env Files**: It can also load environment variables from `.env` files. It will look for these files in two locations:
    *   A project-specific `.env` file in the root of the project directory.
    *   A user-specific `.env` file at `~/.semfire/.env`.

The `~/.semfire` directory is only created when a configuration is explicitly saved by the user, not on initial startup.

Currently, the application only supports OpenAI out of the box. A `GEMINI_API_KEY` or other keys will not be used unless a new provider is implemented in the code.

## How do the non-AI detectors work?

The non-AI detection is handled by three main detectors:

### Rule-Based Detector (`RuleBasedDetector`)

This detector scans text for specific keywords and phrases that are categorized into predefined rule sets. The default rules include:

*   **scheming**: Keywords related to deception (e.g., "hide", "pretend", "deceive").
*   **indirect_reference**: Phrases that refer back to previous points (e.g., "as you said", "building on").
*   **context_steering**: Phrases that attempt to guide the conversation in a specific direction (e.g., "what if", "imagine that").
*   **knowledge_asymmetry**: Keywords that suggest the user has information the AI doesn't (e.g., "they don't know").

The detector calculates a score based on how many of these keywords are found in the current message and the conversation history.

### Heuristic Detector (`HeuristicDetector`)

This detector uses broader, more general characteristics of the text to identify potential manipulation. Its heuristics include:

*   **Text Length**: The length of the input text is used to determine a base score (e.g., very short, medium, or long text).
*   **Urgency Keywords**: It looks for words that create a sense of urgency (e.g., "urgent", "critical") and increases the score if they are found.
*   **Conversation History**: The presence of a longer conversation history can also slightly increase the score.

The final classification can be flagged as "potentially_manipulative_heuristic" if the combined score crosses a certain threshold.

### Injection Detector (`InjectionDetector`)

This is another rule-based detector, but it is highly specialized for detecting "prompt injection" attacks. It looks for specific, well-known phrases that are used to try and hijack the AI's instructions. The rules include:

*   **instruction_manipulation**: Phrases like "ignore your previous instructions".
*   **role_play_attack**: Phrases like "you are now" or "act as".

If any of these phrases are detected, it classifies the input as a "potential_injection".

## How to Configure LLM Providers

SemFire can be configured to use different Large Language Model (LLM) providers. The configuration can be managed in two primary ways:

1.  **Environment Variables**: You can set environment variables directly in your shell or through a `.env` file. This is the recommended way to handle sensitive API keys.
2.  **Configuration File**: You can create a `config.json` file in the `~/.semfire/` directory. This file allows for more detailed configuration.

The application uses the following priority for configuration:
1.  `SEMFIRE_LLM_PROVIDER` environment variable.
2.  `provider` setting in `config.json`.
3.  Auto-detection based on the presence of API keys in the environment.

### OpenAI

*   **API Key Environment Variable**: `OPENAI_API_KEY`
*   **Example `config.json`**:
    ```json
    {
      "provider": "openai",
      "openai": {
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY"
      }
    }
    ```

### Gemini

*   **API Key Environment Variable**: `GEMINI_API_KEY`
*   **Example `config.json`**:
    ```json
    {
      "provider": "gemini",
      "gemini": {
        "model": "gemini-1.5-flash-latest",
        "api_key_env": "GEMINI_API_KEY"
      }
    }
    ```

### OpenRouter

*   **API Key Environment Variable**: `OPENROUTER_API_KEY`
*   **Example `config.json`**:
    ```json
    {
      "provider": "openrouter",
      "openrouter": {
        "model": "deepseek/deepseek-chat",
        "api_key_env": "OPENROUTER_API_KEY"
      }
    }
    ```

### Perplexity

*   **API Key Environment Variable**: `PERPLEXITY_API_KEY`
*   **Example `config.json`**:
    ```json
    {
      "provider": "perplexity",
      "perplexity": {
        "model": "sonar-medium-online",
        "api_key_env": "PERPLEXITY_API_KEY"
      }
    }
    ```

### Transformers (Placeholder)

The `transformers` LLM provider is currently a placeholder. While it is listed as a configurable option, the actual implementation for loading and interacting with models from the Hugging Face `transformers` library is not yet present.

**Regarding Hugging Face API Keys:**
For local models specified via `model_path`, a Hugging Face API key is generally *not* required. However, if the future implementation were to involve directly fetching models from the Hugging Face Hub without prior local download, or utilizing private models or paid services, a Hugging Face token or API key might become necessary.

To fully implement the `transformers` provider, the following steps are required:
1.  **Create a `TransformersProvider` class:** This class should inherit from `LLMProviderBase` and encapsulate the logic for loading a `transformers` model and tokenizer (e.g., using `AutoModelForCausalLM` and `AutoTokenizer`) based on the `model_path` and `device` specified in the configuration.
2.  **Implement `is_ready()` and `generate()` methods:**
    *   `is_ready()`: Should verify that the model and tokenizer have been successfully loaded.
    *   `generate(prompt: str)`: Should take a prompt string, tokenize it, pass it to the loaded `transformers` model for inference, and return the generated text.
3.  **Integrate into `load_llm_provider_from_config()`:** Add a conditional branch within the `load_llm_provider_from_config()` function to detect when `provider == "transformers"` and then instantiate and return an instance of the `TransformersProvider` class, passing in the `model_path` and `device` from the configuration.

