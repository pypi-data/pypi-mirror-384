
import os
import sys

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from detectors.llm_provider import (
    load_llm_provider_from_config,
    _read_config,
    _load_env_file_into_process,
    OpenAIProvider,
)

def _test_single_provider(provider_name: str):
    """
    Tests a single provider by temporarily setting the environment variable.
    """
    print(f"--- Testing: {provider_name.capitalize()} ---")
    
    # Temporarily set env var to force provider choice
    original_env = os.environ.get("SEMFIRE_LLM_PROVIDER")
    os.environ["SEMFIRE_LLM_PROVIDER"] = provider_name
    
    provider = load_llm_provider_from_config()
    
    # Restore environment
    if original_env is None:
        if "SEMFIRE_LLM_PROVIDER" in os.environ:
             del os.environ["SEMFIRE_LLM_PROVIDER"]
    else:
        os.environ["SEMFIRE_LLM_PROVIDER"] = original_env

    if provider and provider.is_ready():
        model = getattr(provider, 'model', 'N/A')
        print(f"Status: 🟢 OK")
        print(f"  - Model: {model}")
        if isinstance(provider, OpenAIProvider) and provider.base_url:
             print(f"  - Base URL: {provider.base_url}")
    else:
        print(f"Status: 🔴 Not Configured")
        # Provide a reason
        config = _read_config()
        provider_config = config.get(provider_name, {})
        api_key_env = provider_config.get("api_key_env", f"{provider_name.upper()}_API_KEY")
        if not os.environ.get(api_key_env):
            print(f"  - Reason: Environment variable '{api_key_env}' is not set.")
        else:
            print(f"  - Reason: Provider failed to initialize. Check your config file for the correct model name or other settings.")

    print("-" * 20)


def _test_transformers():
    """
    Special case for testing the Transformers provider configuration.
    """
    print("--- Testing: Transformers ---")
    config = _read_config()
    
    # To test transformers, we must check the config directly, as it might not be the auto-detected provider
    transformers_config = config.get("transformers", {})
    model_path = transformers_config.get("model_path")

    if not model_path:
        print(f"Status: 🔴 Not Configured")
        print(f"  - Reason: 'model_path' is not defined in the [transformers] section of the config file.")
    elif os.path.exists(model_path):
        print(f"Status: 🟢 OK")
        print(f"  - Model Path: {model_path}")
        print(f"  - Device: {transformers_config.get('device', 'cpu')}")
    else:
        print(f"Status: 🔴 Not Configured")
        print(f"  - Reason: The model path '{model_path}' does not exist.")
    print("-" * 20)


def _main():
    """
    Main function to run all provider tests.
    """
    print("Starting LLM Provider Configuration Test...")
    print("-" * 40)

    # Load environment variables from .env files
    _load_env_file_into_process()
    print("Loaded environment variables from .env files (if present).")
    print("-" * 40)

    providers_to_test = ["openai", "gemini", "openrouter", "perplexity"]
    for provider in providers_to_test:
        test_provider(provider)
    
    test_transformers()


if __name__ == "__main__":
    _main()
