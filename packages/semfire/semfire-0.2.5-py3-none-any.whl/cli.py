import argparse
import sys
import os
import json

# Ensure local imports work when running via `python -m src.cli` without install
_SRC_DIR = os.path.dirname(__file__)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from semantic_firewall import SemanticFirewall, __version__
from detectors.llm_provider import write_config, get_config_summary
from config_menu import run_config_menu

 

def _read_text_from_args(args: argparse.Namespace) -> str:
    if getattr(args, "text", None):
        return args.text
    if getattr(args, "file", None):
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if getattr(args, "stdin", False):
        return sys.stdin.read()
    raise SystemExit("No input provided. Use positional TEXT, --file, or --stdin.")

def _handle_analyze(args: argparse.Namespace) -> None:
    firewall = SemanticFirewall()
    text = _read_text_from_args(args)
    history = args.history if args.history else []

    results = firewall.analyze_conversation(
        current_message=text,
        conversation_history=history,
    )

    which = getattr(args, "detector", None)
    if which:
        alias = {
            "rule-based": "rule",
            "echo-chamber": "echo",
            "inj": "injection",
            "injectiondetector": "injection",
        }
        which = alias.get(which, which)

    if which and which != "all":
        key_map = {
            "rule": "RuleBasedDetector",
            "heuristic": "HeuristicDetector",
            "echo": "EchoChamberDetector",
            "injection": "InjectionDetector",
        }
        sel = results.get(key_map[which], {})
        print(json.dumps(sel))
    else:
        print(json.dumps(results))

    if not getattr(args, "json_only", False):
        is_manipulative_flag = firewall.is_manipulative(
            current_message=text,
            conversation_history=history,
            threshold=getattr(args, "threshold", 0.75),
        )
        print(f"\nOverall manipulative assessment (default threshold): {is_manipulative_flag}")

def _handle_spotlight(args: argparse.Namespace) -> None:
    try:
        from spotlighting import Spotlighter
    except ImportError:
        from spotlighting.defenses import Spotlighter

    # Build options and resolve optional positional parameter for datamark
    opts = {}
    if args.method == "delimit":
        opts = {"start": args.start, "end": args.end}
    elif args.method == "datamark":
        marker = args.marker or getattr(args, "param", None)
        if marker:
            opts = {"marker": marker}

    # Determine text input with flexible positional handling
    if getattr(args, "text", None):
        text = args.text
    elif args.method != "datamark" and getattr(args, "param", None):
        text = args.param
    else:
        text = _read_text_from_args(args)

    spot = Spotlighter(method=args.method, **opts)
    print(spot.process(text))

def _handle_detector_list(_: argparse.Namespace) -> None:
    """List available detectors by shorthand name."""
    print("\n".join(["rule", "heuristic", "echo", "injection"]))

def _handle_detector_run(args: argparse.Namespace) -> None:
    """Run a single detector via the same machinery as `analyze`.

    This keeps output structure consistent with other CLI calls while
    giving detectors their own subcommands/flags.
    """
    firewall = SemanticFirewall()
    text = _read_text_from_args(args)
    history = args.history if getattr(args, "history", None) else []

    # Reuse the combined pipeline and slice the requested detector for consistency
    results = firewall.analyze_conversation(
        current_message=text,
        conversation_history=history,
    )

    key_map = {
        "rule": "RuleBasedDetector",
        "heuristic": "HeuristicDetector",
        "echo": "EchoChamberDetector",
        "injection": "InjectionDetector",
    }
    detector_class_name = key_map[args.detector]
    sel = results.get(detector_class_name, {})
    # Add the detector_name to the output
    sel["detector_name"] = detector_class_name
    print(json.dumps(sel))

def main():
    prog = os.path.basename(sys.argv[0]).lower()
    if "aegis" in prog:
        print(
            "Deprecation notice: 'aegis' CLI is deprecated; use 'semfire' instead.",
            file=sys.stderr,
        )

    parser = argparse.ArgumentParser(description="SemFire: Semantic Firewall CLI.")
    parser.add_argument("--version", action="version", version=f"semfire {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    config_parser = subparsers.add_parser("config", help="Configure LLM providers.")
    config_parser.add_argument("--provider", choices=["openai", "gemini", "openrouter", "perplexity", "transformers", "none"], help="Set provider.")
    # OpenAI
    config_parser.add_argument("--openai-model", help="OpenAI model name.")
    config_parser.add_argument("--openai-api-key-env", help="Env var holding OpenAI API key (default: OPENAI_API_KEY).")
    config_parser.add_argument("--openai-base-url", help="Custom OpenAI-compatible base URL.")
    # Gemini
    config_parser.add_argument("--gemini-model", help="Gemini model name.")
    config_parser.add_argument("--gemini-api-key-env", help="Env var holding Gemini API key (default: GEMINI_API_KEY).")
    # OpenRouter
    config_parser.add_argument("--openrouter-model", help="OpenRouter model name.")
    config_parser.add_argument("--openrouter-api-key-env", help="Env var holding OpenRouter API key (default: OPENROUTER_API_KEY).")
    # Perplexity
    config_parser.add_argument("--perplexity-model", help="Perplexity model name.")
    config_parser.add_argument("--perplexity-api-key-env", help="Env var holding Perplexity API key (default: PERPLEXITY_API_KEY).")
    # Transformers-specific
    config_parser.add_argument("--transformers-model-path", help="HF model ID or local path for transformers provider.")
    config_parser.add_argument("--transformers-device", help="Device for transformers provider (cpu/cuda).", default=None)
    # General
    config_parser.add_argument("--non-interactive", action="store_true", help="Do not launch the interactive menu.")
    

    spotlight_parser = subparsers.add_parser("spotlight", help="Transform text with defenses.")
    spotlight_parser.add_argument("method", choices=["delimit", "datamark", "base64", "rot13", "binary", "layered"], help="Spotlighting method.")
    spotlight_parser.add_argument("param", nargs="?", help="Optional method parameter (e.g., marker for datamark).")
    spotlight_parser.add_argument("text", nargs="?", help="The text to transform.")
    spotlight_parser.add_argument("--file", help="Read input from a file.")
    spotlight_parser.add_argument("--stdin", action="store_true", help="Read input from stdin.")
    spotlight_parser.add_argument("--start", default="«", help="Start delimiter.")
    spotlight_parser.add_argument("--end", default="»", help="End delimiter.")
    spotlight_parser.add_argument("--marker", help="Datamark marker.")
    spotlight_parser.set_defaults(func=_handle_spotlight)

    # detector
    detector_parser = subparsers.add_parser(
        "detector",
        help="Run individual detectors.",
        description="Detector-specific commands and flags.",
    )
    det_sub = detector_parser.add_subparsers(dest="detector_cmd", help="Detector subcommands")

    # detector list
    det_list = det_sub.add_parser("list", help="List available detectors.")
    det_list.set_defaults(func=_handle_detector_list)

    # detector <name>
    for det in ("rule", "heuristic", "echo", "injection"):
        d = det_sub.add_parser(det, help=f"Run the {det} detector.")
        # input handling flags
        d.add_argument("text", nargs="?", help="The text input to analyze.")
        d.add_argument("--file", help="Read input from a file.")
        d.add_argument("--stdin", action="store_true", help="Read input from stdin.")
        d.add_argument("--history", nargs="*", help="Conversation history.")
        d.set_defaults(func=_handle_detector_run, detector=det)


    
    analyze_parser = subparsers.add_parser("analyze", help="Analyze text for deception cues.")
    analyze_parser.add_argument("text", nargs="?", help="The text input to analyze (e.g., current message).")
    analyze_parser.add_argument("--file", help="Read input from a file.")
    analyze_parser.add_argument("--stdin", action="store_true", help="Read input from stdin.")
    analyze_parser.add_argument("--history", nargs="*", help="Conversation history.")
    analyze_parser.add_argument("--json-only", action="store_true", help="Only JSON output.")
    analyze_parser.add_argument("--threshold", type=float, default=0.75, help="Manipulation threshold.")
    analyze_parser.add_argument(
        "--detector",
        choices=["all", "rule", "heuristic", "echo", "injection", "rule-based", "echo-chamber", "inj", "injectiondetector"],
        help="Optional: run a single detector (default: all)",
    )
    analyze_parser.set_defaults(func=_handle_analyze)

    def config_command(args):
        if any([
            args.provider,
            # OpenAI
            args.openai_model, args.openai_api_key_env, args.openai_base_url,
            # Gemini
            getattr(args, "gemini_model", None), getattr(args, "gemini_api_key_env", None),
            # OpenRouter
            getattr(args, "openrouter_model", None), getattr(args, "openrouter_api_key_env", None),
            # Perplexity
            getattr(args, "perplexity_model", None), getattr(args, "perplexity_api_key_env", None),
            # Transformers
            args.transformers_model_path, args.transformers_device,
        ]):
            prov = args.provider or "openai"
            path = write_config(
                provider=prov,
                openai_model=args.openai_model,
                openai_api_key_env=args.openai_api_key_env,
                openai_base_url=args.openai_base_url,
                gemini_model=getattr(args, "gemini_model", None),
                gemini_api_key_env=getattr(args, "gemini_api_key_env", None),
                openrouter_model=getattr(args, "openrouter_model", None),
                openrouter_api_key_env=getattr(args, "openrouter_api_key_env", None),
                perplexity_model=getattr(args, "perplexity_model", None),
                perplexity_api_key_env=getattr(args, "perplexity_api_key_env", None),
                transformers_model_path=args.transformers_model_path,
                transformers_device=args.transformers_device,
            )
            print(f"Config saved to {path}")
            print(f"Active: {get_config_summary()}")
        else:
            # Respect non-interactive environments or explicit flag
            if getattr(args, "non_interactive", False):
                print("Non-interactive mode: skipping menu.\n" + get_config_summary())
            else:
                try:
                    run_config_menu(non_interactive=False)
                except EOFError:
                    # Graceful fallback when no input stream is available
                    print("No input available; skipping interactive menu.")
                print(f"Active: {get_config_summary()}")

    config_parser.set_defaults(func=config_command)

    args = parser.parse_args()

    if getattr(args, 'command', None) is None:
        parser.print_help(sys.stderr)
        parser.exit(status=2)

    args.func(args)

if __name__ == "__main__":
    main()
