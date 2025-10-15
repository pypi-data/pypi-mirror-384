import os
import time
import getpass
from typing import Dict

try:
    from colorama import Fore, Style  # type: ignore
except Exception:  # fallback to no-color
    class _No:
        RED = GREEN = CYAN = BRIGHT = RESET_ALL = ""
    Fore = Style = _No()

try:
    from dotenv import set_key, dotenv_values  # type: ignore
except Exception:
    # Minimal stubs if python-dotenv is not present; write simple KEY=VAL to .env
    def dotenv_values(fp: str = ".env") -> Dict[str, str]:
        vals: Dict[str, str] = {}
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
        except Exception:
            pass
        return vals

    def set_key(fp: str, key: str, value: str):
        lines = []
        found = False
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        lines.append(f"{key}={value}\n")
                        found = True
                    else:
                        lines.append(line)
        except FileNotFoundError:
            pass
        if not found:
            lines.append(f"{key}={value}\n")
        with open(fp, "w", encoding="utf-8") as f:
            f.writelines(lines)


def _current_provider() -> str:
    return os.environ.get("SEMFIRE_LLM_PROVIDER", "").strip()


def _mask(val: str) -> str:
    if not val:
        return "Not Set"
    return f"****{val[-4:]}"


def test_api_keys() -> Dict[str, bool]:
    cfg = dotenv_values('.env')
    def val(name):
        return (os.getenv(name) or cfg.get(name) or "").strip()
    gk = val("GEMINI_API_KEY")
    ok = val("OPENAI_API_KEY")
    ork = val("OPENROUTER_API_KEY")
    pk = val("PERPLEXITY_API_KEY")
    gemini_ok = gk.startswith("AIza") and len(gk) >= 20 if gk else False
    openai_ok = ok.startswith("sk-") and len(ok) >= 20 if ok else False
    openrouter_ok = ork.startswith("sk-or-") and len(ork) >= 20 if ork else False
    perplexity_ok = pk.startswith("pplx-") and len(pk) >= 15 if pk else False
    return {"gemini": gemini_ok, "openai": openai_ok, "openrouter": openrouter_ok, "perplexity": perplexity_ok}


def run_config_menu() -> None:
    statuses = test_api_keys()
    if not any(statuses.values()):
        print(f"{Fore.RED}Warning: No valid API keys found. Without a valid API key, you will just be string matching against a single suggested answer.{Style.RESET_ALL}")

    print(f"\n{Style.BRIGHT}{Fore.CYAN}--- API Key Configuration ---")
    config = dotenv_values(".env")
    gemini_key = config.get("GEMINI_API_KEY", "Not Set")
    openai_key = config.get("OPENAI_API_KEY", "Not Set")
    openrouter_key = config.get("OPENROUTER_API_KEY", "Not Set")
    perplexity_key = config.get("PERPLEXITY_API_KEY", "Not Set")

    statuses = test_api_keys()
    gemini_display = f"{Fore.GREEN}{_mask(gemini_key)} (Valid){Style.RESET_ALL}" if statuses["gemini"] else f"{Fore.RED}{_mask(gemini_key)} (Invalid){Style.RESET_ALL}"
    openai_display = f"{Fore.GREEN}{_mask(openai_key)} (Valid){Style.RESET_ALL}" if statuses["openai"] else f"{Fore.RED}{_mask(openai_key)} (Invalid){Style.RESET_ALL}"
    openrouter_display = f"{Fore.GREEN}{_mask(openrouter_key)} (Valid){Style.RESET_ALL}" if statuses["openrouter"] else f"{Fore.RED}{_mask(openrouter_key)} (Invalid){Style.RESET_ALL}"
    perplexity_display = f"{Fore.GREEN}{_mask(perplexity_key)} (Valid){Style.RESET_ALL}" if statuses.get("perplexity") else f"{Fore.RED}{_mask(perplexity_key)} (Invalid){Style.RESET_ALL}"

    print(f"  {Style.BRIGHT}1.{Style.RESET_ALL} Set Gemini API Key (current: {gemini_display}) (Model: gemini-1.5-flash-latest)")
    print(f"  {Style.BRIGHT}2.{Style.RESET_ALL} Set OpenAI API Key (current: {openai_display}) (Model: gpt-3.5-turbo)")
    print(f"  {Style.BRIGHT}3.{Style.RESET_ALL} Set OpenRouter API Key (current: {openrouter_display}) (Model: deepseek/deepseek-r1-0528:free)")
    print(f"  {Style.BRIGHT}4.{Style.RESET_ALL} Set Perplexity API Key (current: {perplexity_display}) (Model: sonar-medium-online)")

    provider = _current_provider()
    provider_display = f"{Fore.GREEN}{provider}{Style.RESET_ALL}" if provider else f"{Fore.RED}None{Style.RESET_ALL}"

    print(f"\n{Style.BRIGHT}{Fore.CYAN}--- AI Provider Selection ---")
    print(f"  {Style.BRIGHT}5.{Style.RESET_ALL} Choose AI Provider (current: {provider_display})")
    print(f"  {Style.BRIGHT}6.{Style.RESET_ALL} Back")

    while True:
        choice = input("Enter your choice: ").strip()
        if choice == '1':
            key = getpass.getpass("Enter your Gemini API Key: ").strip()
            if key:
                set_key(".env", "GEMINI_API_KEY", key)
                os.environ["GEMINI_API_KEY"] = key
                print("\nGemini API Key saved.")
                statuses = test_api_keys()
                if not statuses.get("gemini", False):
                    print(f"{Fore.RED}Invalid Gemini API Key. Please check your key.{Style.RESET_ALL}")
            else:
                print("\nNo key entered.")
            time.sleep(1)
            break
        elif choice == '2':
            key = input("Enter your OpenAI API Key: ").strip()
            if key:
                set_key(".env", "OPENAI_API_KEY", key)
                os.environ["OPENAI_API_KEY"] = key
                print("\nOpenAI API Key saved.")
                statuses = test_api_keys()
                if not statuses.get("openai", False):
                    print(f"{Fore.RED}Invalid OpenAI API Key. Please check your key.{Style.RESET_ALL}")
            else:
                print("\nNo key entered.")
            time.sleep(1)
            break
        elif choice == '3':
            key = input("Enter your OpenRouter API Key: ").strip()
            if key:
                set_key(".env", "OPENROUTER_API_KEY", key)
                os.environ["OPENROUTER_API_KEY"] = key
                print("\nOpenRouter API Key saved.")
                statuses = test_api_keys()
                if not statuses.get("openrouter", False):
                    print(f"{Fore.RED}Invalid OpenRouter API Key. Please check your key.{Style.RESET_ALL}")
            else:
                print("\nNo key entered.")
            time.sleep(1)
            break
        elif choice == '4':
            key = input("Enter your Perplexity API Key: ").strip()
            if key:
                set_key(".env", "PERPLEXITY_API_KEY", key)
                os.environ["PERPLEXITY_API_KEY"] = key
                print("\nPerplexity API Key saved.")
                statuses = test_api_keys()
                if not statuses.get("perplexity", False):
                    print(f"{Fore.RED}Invalid Perplexity API Key. Please check your key.{Style.RESET_ALL}")
            else:
                print("\nNo key entered.")
            time.sleep(1)
            break
        elif choice == '5':
            print("\nSelect AI Provider:")
            print("  1. openrouter")
            print("  2. gemini")
            print("  3. openai")
            print("  4. perplexity")
            print("  5. none (disable AI)")
            sub = input("Enter your choice: ").strip()
            mapping = {'1': 'openrouter', '2': 'gemini', '3': 'openai', '4': 'perplexity', '5': ''}
            if sub in mapping:
                sel = mapping[sub]
                # Store under SemFire provider environment variable
                set_key(".env", "SEMFIRE_LLM_PROVIDER", sel)
                os.environ["SEMFIRE_LLM_PROVIDER"] = sel
                print(f"\nAI Provider set to {sel or 'none'}.")
            else:
                print("\nInvalid selection.")
            time.sleep(1)
            break
        elif choice == '6':
            return
        else:
            print("Invalid choice. Please try again.")
