import os
import sys
import time
import getpass
from typing import Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner

try:
    from dotenv import set_key, dotenv_values
except ImportError:
    # Minimal stubs if python-dotenv is not present
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
        except FileNotFoundError:
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


console = Console()


def _current_provider() -> str:
    return os.environ.get("SEMFIRE_LLM_PROVIDER", "").strip()


def _mask(val: str) -> str:
    if not val or val == "Not Set":
        return "[red]Not Set[/red]"
    return f"****{val[-4:]}"


def test_api_keys() -> Dict[str, bool]:
    cfg = dotenv_values('.env')
    def val(name):
        return (os.getenv(name) or cfg.get(name) or "").strip()
    
    # Basic validation checks
    # Note: These are not foolproof and don't guarantee the key is actually valid on the service side.
    # They are just simple heuristics to catch common mistakes.
    gk = val("GEMINI_API_KEY")
    ok = val("OPENAI_API_KEY")
    ork = val("OPENROUTER_API_KEY")
    pk = val("PERPLEXITY_API_KEY")
    
    gemini_ok = gk.startswith("AIza") and len(gk) >= 20 if gk else False
    openai_ok = ok.startswith("sk-") and len(ok) >= 20 if ok else False
    openrouter_ok = ork.startswith("sk-or-") and len(ork) >= 20 if ork else False
    perplexity_ok = pk.startswith("pplx-") and len(pk) >= 15 if pk else False
    
    return {"gemini": gemini_ok, "openai": openai_ok, "openrouter": openrouter_ok, "perplexity": perplexity_ok}


def run_config_menu(non_interactive: bool = False) -> None:
    # In non-interactive environments, avoid prompting to prevent EOFError
    if non_interactive or not console.is_interactive or not sys.stdin.isatty():
        console.print(Panel(
            "[yellow]Non-interactive environment detected.[/yellow]\n"
            "Use CLI flags (e.g., 'semfire config --provider openai --openai-model gpt-4o-mini --openai-api-key-env OPENAI_API_KEY')\n"
            "or set environment variables / .env values directly.",
            title="[bold red]Config: Non-Interactive[/bold red]",
            border_style="red",
        ))
        return
    statuses = test_api_keys()
    if not any(statuses.values()):
        console.print(Panel("[yellow]Warning:[/yellow] No valid API keys found. Without a valid API key, the application will fall back to simple string matching against a single suggested answer.",
                            title="[bold red]API Key Missing[/bold red]", border_style="yellow"))

    while True:
        console.clear()
        table = Table(title="[bold cyan]API Key Configuration[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="dim", width=6)
        table.add_column("Service", style="bold")
        table.add_column("Key Status", justify="right")
        table.add_column("Model", style="green")

        config = dotenv_values(".env")
        keys = {
            "Gemini": config.get("GEMINI_API_KEY", "Not Set"),
            "OpenAI": config.get("OPENAI_API_KEY", "Not Set"),
            "OpenRouter": config.get("OPENROUTER_API_KEY", "Not Set"),
            "Perplexity": config.get("PERPLEXITY_API_KEY", "Not Set"),
        }
        models = {
            "Gemini": "gemini-1.5-flash-latest",
            "OpenAI": "gpt-3.5-turbo",
            "OpenRouter": "deepseek/deepseek-r1-0528:free",
            "Perplexity": "sonar-medium-online",
        }
        
        statuses = test_api_keys()
        for i, (service, key) in enumerate(keys.items(), 1):
            status_str = f"[{'green' if statuses.get(service.lower()) else 'red'}]"
            status_str += "Valid" if statuses.get(service.lower()) else "Invalid"
            status_str += f"[/{'green' if statuses.get(service.lower()) else 'red'}]"
            table.add_row(f"[bold]{i}[/bold]", service, f"{_mask(key)} ({status_str})", models[service])

        console.print(table)

        provider = _current_provider()
        provider_display = f"[green]{provider}[/green]" if provider else "[red]None[/red]"

        console.print("\n[bold cyan]-- AI Provider Selection --[/bold cyan]")
        console.print(f"  [bold]5.[/bold] Choose AI Provider (current: {provider_display})")
        console.print("  [bold]6.[/bold] Back")

        try:
            choice = Prompt.ask("Enter your choice", choices=[str(i) for i in range(1, 7)], default="6")
        except EOFError:
            console.print("\n[yellow]No input available; exiting config menu.[/yellow]")
            break

        if choice == '6':
            break

        service_map = {
            '1': ("Gemini", "GEMINI_API_KEY"),
            '2': ("OpenAI", "OPENAI_API_KEY"),
            '3': ("OpenRouter", "OPENROUTER_API_KEY"),
            '4': ("Perplexity", "PERPLEXITY_API_KEY"),
        }

        if choice in service_map:
            service_name, key_name = service_map[choice]
            try:
                key = Prompt.ask(f"Enter your {service_name} API Key", password=True)
            except EOFError:
                console.print("\n[yellow]No input available; skipping key entry.[/yellow]")
                key = ""
            if key:
                with Live(Spinner("dots"), console=console, transient=True) as live:
                    live.start()
                    set_key(".env", key_name, key)
                    os.environ[key_name] = key
                    time.sleep(1) # Simulate saving
                    live.stop()
                console.print(f"\n[green]{service_name} API Key saved.[/green]")
                if not test_api_keys().get(service_name.lower()):
                    console.print(f"[red]Invalid {service_name} API Key. Please check your key.[/red]")
            else:
                console.print("\n[yellow]No key entered.[/yellow]")
            time.sleep(1)

        elif choice == '5':
            console.print("\n[bold]Select AI Provider:[/bold]")
            provider_table = Table(show_header=False, pad_edge=False, box=None)
            provider_table.add_column(style="dim", width=4)
            provider_table.add_column()
            providers = ["openrouter", "gemini", "openai", "perplexity", "none"]
            for i, p in enumerate(providers, 1):
                provider_table.add_row(f"[bold]{i}[/bold]", p)
            console.print(provider_table)
            
            try:
                sub_choice = Prompt.ask("Enter your choice", choices=[str(i) for i in range(1, 6)], default="5")
            except EOFError:
                console.print("\n[yellow]No input available; keeping current provider.[/yellow]")
                sub_choice = "5"
            selected_provider = providers[int(sub_choice) - 1] if sub_choice else "none"
            
            set_key(".env", "SEMFIRE_LLM_PROVIDER", selected_provider if selected_provider != "none" else "")
            os.environ["SEMFIRE_LLM_PROVIDER"] = selected_provider if selected_provider != "none" else ""
            console.print(f"\n[green]AI Provider set to {selected_provider}.[/green]")
            time.sleep(1)

if __name__ == '__main__':
    run_config_menu()
