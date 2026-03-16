#!/usr/bin/env python3
"""
OpenCode Model Manager - Interactive CLI for managing subagent models.

Workflow:
1. Fetch models from models.dev
2. Filter by whitelisted/blacklisted providers
3. For authenticated providers, check if model is free via provider API
4. Filter to only free models, sorted by benchmark score
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

BENCHMARK_SCORES = {
    # LiveCodeBench / SWE-Bench scores (primary)
    "grok-3": 79.4,
    "grok-3-mini": 74.0,
    "grok-4": 85.0,
    "grok-4-20b": 80.0,
    "grok-code-fast": 75.0,
    "grok-4.1": 82.0,
    "grok-4-fast": 78.0,
    "gemini-2.5-pro": 79.4,
    "gemini-2.5-flash": 75.6,
    "gemini-2.5-flash-lite": 70.7,
    "gemini-2.0-flash": 63.9,
    "gemini-2.0-pro": 68.0,
    "gemini-3-pro": 79.7,
    "gemini-3-flash": 76.0,
    "gemini-1.5-pro": 72.0,
    "gemini-1.5-flash": 65.0,
    "llama-3.3-70b": 70.0,
    "llama-3.1-405b": 68.0,
    "llama-3.1-70b": 65.0,
    "llama-3.1-8b": 45.0,
    "llama-3-70b": 65.0,
    "llama-3-8b": 42.0,
    "llama-3.2-90b": 72.0,
    "llama-3.2-70b": 68.0,
    "llama-3.2-3b": 45.0,
    "llama-2-70b": 50.0,
    "mistral-large": 72.0,
    "mistral-small": 55.0,
    "mistral-small-3.1": 60.0,
    "mixtral-8x7b": 50.0,
    "mixtral-8x22b": 58.0,
    "qwen-3-235b": 78.0,
    "qwen-3-32b": 65.0,
    "qwen-3-14b": 55.0,
    "qwen-3-8b": 48.0,
    "qwen-3-4b": 40.0,
    "qwen-2.5-coder-32b": 60.0,
    "qwen-2.5vl-32b": 58.0,
    "qwen-2.5-coder-14b": 52.0,
    "deepseek-v3": 70.0,
    "deepseek-r1": 72.0,
    "deepseek-coder-v2": 68.0,
    "deepseek-chat": 65.0,
    "claude-sonnet-4": 74.0,
    "claude-sonnet-4.5": 76.0,
    "claude-opus-4.5": 78.0,
    "claude-opus-4.6": 80.0,
    "claude-haiku-4": 50.0,
    "claude-haiku-4.5": 52.0,
    "gpt-4o": 72.0,
    "gpt-4o-mini": 55.0,
    "gpt-4o-audio": 70.0,
    "gpt-5": 76.0,
    "gpt-5.1": 74.0,
    "gpt-5.2": 78.0,
    "gpt-4.1": 70.0,
    "gpt-4.1-mini": 58.0,
    "o3-mini": 75.0,
    "o4-mini": 72.0,
    "kimi-k2": 79.7,
    "kimi-k2.5": 79.7,
    "kimi-k2-thinking": 83.1,
    "kimi-k1.5": 75.0,
    "glm-5": 74.0,
    "glm-4.5": 68.0,
    "glm-4": 60.0,
    "glm-4-vision": 62.0,
    "minimax-m2.5": 75.0,
    "minimax-m2.1": 65.0,
    "minimax-m2": 60.0,
    "command-r-plus": 55.0,
    "command-r": 45.0,
    "command-r7b": 42.0,
    "gemma-3-27b": 59.0,
    "gemma-3-4b": 40.0,
    "gemma-3-12b": 50.0,
    "gemma-3n-4b": 45.0,
    "gemma-3n-2b": 38.0,
    "gemma-2-27b": 50.0,
    "gemma-2-9b": 38.0,
    "gemma-2-2b": 32.0,
    "phi-4": 52.0,
    "phi-3.5-mini": 48.0,
    "phi-3.5": 45.0,
    "phi-3": 40.0,
    "phi-2": 35.0,
    "nemotron-3-super": 55.0,
    "nemotron-3-nano": 45.0,
    "nemotron-4-super": 65.0,
    "nemotron-4-mini": 52.0,
    "trinity-large": 50.0,
    "trinity-mini": 40.0,
    "step-3.5-flash": 55.0,
    "step-2-flash": 48.0,
    "devstral-2": 58.0,
    "seed-2.0-pro": 72.0,
    "seed-2.0-thinking": 75.0,
    "olmo-2-13b": 48.0,
    "olmo-2-7b": 42.0,
    "hermes-3": 68.0,
    "aya-expanse": 45.0,
    "carbon-enterprise": 55.0,
    "jamba-1.5-large": 58.0,
    "jamba-1.5-mini": 50.0,
    "jamba-2": 62.0,
    "aya-vision": 48.0,
    "sea Pearl": 45.0,
    "c4ai-aya-expanse": 45.0,
    "falcon-3": 48.0,
    "falcon-3-mamba": 50.0,
}

# Fallback scoring based on model family and size
MODEL_FAMILY_BONUS = {
    "grok": 5.0,
    "gemini": 3.0,
    "claude": 8.0,
    "gpt": 5.0,
    "llama": 2.0,
    "qwen": 4.0,
    "deepseek": 4.0,
    "mistral": 2.0,
    "kimi": 4.0,
    "glm": 3.0,
    "minimax": 4.0,
    "command": 1.0,
    "gemma": 1.0,
    "phi": 1.0,
    "nemotron": 2.0,
    "hermes": 3.0,
    "olmo": 1.0,
    "jamba": 2.0,
    "aya": 1.0,
    "trinity": 1.0,
    "devstral": 2.0,
    "step": 2.0,
    "seed": 3.0,
}

DEFAULT_CONFIG = {
    "providers": {"include": [], "exclude": []},
    "models": {"whitelist": [], "blacklist": []},
    "defaults": {"min_context_window": 200000, "preferred_model": ""},
}


def load_jsonc(path: Path) -> dict:
    """Load JSONC file, stripping comments."""
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    content = path.read_text()

    content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return DEFAULT_CONFIG.copy()


def fetch_models_dev() -> dict:
    """Fetch all models from models.dev API."""
    import urllib.request

    url = "https://models.dev/api.json"
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "curl/8.0")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error: Could not fetch models.dev: {e}")
        return {}


def get_opencode_auth() -> dict:
    """Get authenticated providers from OpenCode auth file."""
    auth_file = Path.home() / ".local/share/opencode/auth.json"
    if not auth_file.exists():
        return {}
    try:
        return json.loads(auth_file.read_text())
    except:
        return {}


def fetch_provider_models(provider: str, api_key: Optional[str] = None) -> list:
    """Fetch models from a specific provider's API."""
    import urllib.request

    if not api_key:
        api_key = os.environ.get(f"{provider.upper()}_API_KEY")

    endpoints = {
        "groq": "https://api.groq.com/openai/v1/models",
        "openai": "https://api.openai.com/v1/models",
        "anthropic": "https://api.anthropic.com/v1/models",
        "google": "https://generativelanguage.googleapis.com/v1/models",
        "mistral": "https://api.mistral.ai/v1/models",
        "cohere": "https://api.cohere.com/v1/models",
        "ai21": "https://api.ai21.com/v1/models",
    }

    url = endpoints.get(provider.lower())
    if not url:
        return []

    try:
        req = urllib.request.Request(url)
        if api_key:
            if provider.lower() == "anthropic":
                req.add_header("x-api-key", api_key)
            elif provider.lower() == "google":
                req.add_header("Authorization", f"Bearer {api_key}")
            else:
                req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if provider.lower() == "google":
                return data.get("models", [])
            return data.get("data", [])
    except Exception:
        return []


def is_model_free_on_provider(
    provider: str, model_id: str, provider_models: list
) -> bool:
    """Check if a model is free on a specific provider."""
    for m in provider_models:
        mid = m.get("id", "")
        if mid == model_id or mid.endswith("/" + model_id):
            # Check pricing
            if provider.lower() == "groq":
                # Groq free tier
                return True
            pricing = m.get("pricing", {})
            if pricing:
                prompt = pricing.get("prompt", "999")
                try:
                    if float(prompt) == 0:
                        return True
                except:
                    pass
            # Check if marked as free
            if m.get("free", False):
                return True
    return False


def get_model_context(model_info: dict) -> int:
    """Extract context window from model info."""
    # Try limit.context first (models.dev format)
    limit = model_info.get("limit", {})
    if isinstance(limit, dict) and "context" in limit:
        return limit["context"]
    if isinstance(limit, dict) and "max_tokens" in limit:
        return limit["max_tokens"]
    if "context_length" in model_info:
        return model_info["context_length"]
    if "contextWindowTokens" in model_info:
        return model_info["contextWindowTokens"]
    if "max_tokens" in model_info:
        return model_info["max_tokens"]
    return 0


def extract_score(model_id: str) -> float:
    """Get benchmark score for a model with fallback heuristics."""
    model_lower = model_id.lower()

    # Check exact match first
    for key, score in BENCHMARK_SCORES.items():
        if key in model_lower:
            return score

    # Fallback: estimate based on model family
    for family, bonus in MODEL_FAMILY_BONUS.items():
        if family in model_lower:
            # Estimate base score from family
            base_score = 30.0 + bonus
            # Add bonus for larger models (if we can detect size)
            if "70b" in model_lower or "72b" in model_lower or "65b" in model_lower:
                base_score += 15
            elif "32b" in model_lower or "30b" in model_lower:
                base_score += 10
            elif "27b" in model_lower:
                base_score += 8
            elif "14b" in model_lower or "13b" in model_lower:
                base_score += 5
            elif "8b" in model_lower or "7b" in model_lower:
                base_score += 2
            elif "3b" in model_lower or "2b" in model_lower:
                base_score += 0
            # Reasoning models get a boost
            if "reasoning" in model_lower or "think" in model_lower:
                base_score += 5
            return min(base_score, 85.0)

    return 0.0


def filter_models_by_provider(models_dev: dict, config: dict) -> list:
    """Filter models by provider whitelist/blacklist."""
    include_providers = config.get("providers", {}).get("include", [])
    exclude_providers = config.get("providers", {}).get("exclude", [])
    whitelist = config.get("models", {}).get("whitelist", [])
    blacklist = config.get("models", {}).get("blacklist", [])
    min_context = config.get("defaults", {}).get("min_context_window", 200000)

    filtered = []

    for provider, provider_data in models_dev.items():
        # Provider filter
        if include_providers and provider not in include_providers:
            continue
        if exclude_providers and provider in exclude_providers:
            continue

        models = provider_data.get("models", {})
        for model_id, model_info in models.items():
            # Model whitelist/blacklist
            if whitelist and model_id not in whitelist:
                continue
            if model_id in blacklist:
                continue

            # Context window filter
            context = get_model_context(model_info)
            if context < min_context:
                continue

            # Get pricing info (models.dev uses 'cost')
            cost = model_info.get("cost", {})
            is_free = False
            if isinstance(cost, dict):
                input_cost = cost.get("input", 999)
                try:
                    is_free = float(input_cost) == 0
                except:
                    is_free = False

            filtered.append(
                {
                    "provider": provider,
                    "model_id": model_id,
                    "name": model_info.get("name", model_id),
                    "context": context,
                    "cost": cost,
                    "free": is_free,
                }
            )

    return filtered


def enrich_with_provider_check(filtered_models: list, auth: dict) -> list:
    """For authenticated providers, verify model is actually available/free."""
    auth = get_opencode_auth()

    # Group models by provider
    by_provider = {}
    for m in filtered_models:
        p = m["provider"]
        if p not in by_provider:
            by_provider[p] = []
        by_provider[p].append(m)

    # For each provider with auth, verify availability
    for provider, models in by_provider.items():
        # Check if we have auth for this provider
        provider_auth = auth.get(provider.lower()) or auth.get(
            provider.replace("-", "_").lower()
        )

        if provider_auth:
            # Fetch provider models
            api_key = provider_auth.get("api_key") or os.environ.get(
                f"{provider.upper()}_API_KEY"
            )
            provider_models = fetch_provider_models(provider, api_key)

            # Update free status
            for m in models:
                if m["free"]:
                    continue  # Already marked free, skip API check
                # Check if model exists and is free on provider
                if is_model_free_on_provider(provider, m["model_id"], provider_models):
                    m["free"] = True
        else:
            # No auth - keep models that are marked free in models.dev
            pass

    return filtered_models


def sort_models(models: list) -> list:
    """Sort models by benchmark score, then by context window."""

    def score_key(m):
        score = extract_score(m["model_id"])
        context = m.get("context", 0)
        return (score, context)

    return sorted(models, key=score_key, reverse=True)


def format_model_line(model: dict, index: int) -> str:
    """Format a model for display."""
    score = extract_score(model["model_id"])
    ctx_k = model.get("context", 0) // 1000
    free_str = " [FREE]" if model.get("free") else ""

    return f"  {index:3d}. [{score:5.1f}] {model['provider']}/{model['model_id']} (ctx: {ctx_k}k){free_str}"


def list_models(config: dict) -> None:
    """List available free models."""
    print("\n=== Fetching models from models.dev ===\n")

    models_dev = fetch_models_dev()
    if not models_dev:
        print("Error: Could not fetch models from models.dev")
        return

    total_models = sum(len(p.get("models", {})) for p in models_dev.values())
    print(f"Total models in database: {total_models}")

    print("\n=== Filtering by provider config ===\n")
    filtered = filter_models_by_provider(models_dev, config)
    print(f"After provider/context filter: {len(filtered)} models")

    print("\n=== Checking free status ===\n")
    auth = get_opencode_auth()
    print(f"Authenticated providers: {list(auth.keys()) if auth else 'None'}")

    enriched = enrich_with_provider_check(filtered, auth)

    # Keep only free models
    free_models = [m for m in enriched if m.get("free")]

    # Sort by benchmark
    sorted_models = sort_models(free_models)

    print(f"Free models available: {len(sorted_models)}\n")

    print("=== Available Free Models (sorted by benchmark) ===\n")

    for i, m in enumerate(sorted_models, 1):
        print(format_model_line(m, i))

    print(f"\nTotal: {len(sorted_models)} free models")


def get_subagents() -> dict:
    """Discover subagents from .opencode/agents/*.md files."""
    agents_dir = Path(".opencode/agents")
    if not agents_dir.exists():
        return {}

    subagents = {}
    for agent_file in agents_dir.glob("*.md"):
        content = agent_file.read_text()

        name_match = re.search(r"^---\s*\nname:\s*(\S+)", content, re.MULTILINE)
        model_match = re.search(r"^model:\s*(.+)$", content, re.MULTILINE)

        if name_match and model_match:
            name = name_match.group(1).strip()
            model = model_match.group(1).strip()
            subagents[name] = model

    return subagents


def update_agent_model(agent_name: str, new_model: str) -> bool:
    """Update the model in an agent's markdown file."""
    agents_dir = Path(".opencode/agents")

    agent_file = None
    for f in agents_dir.glob("*.md"):
        content = f.read_text()
        name_match = re.search(r"^---\s*\nname:\s*(\S+)", content, re.MULTILINE)
        if name_match and name_match.group(1).strip() == agent_name:
            agent_file = f
            break

    if not agent_file:
        print(f"Error: Agent '{agent_name}' not found")
        return False

    content = agent_file.read_text()

    new_content = re.sub(
        r"^(model:\s*).+$", f"\\1{new_model}", content, flags=re.MULTILINE
    )

    agent_file.write_text(new_content)
    return True


def select_model(config: dict) -> Optional[str]:
    """Interactive model selection."""
    print("\n=== Fetching models from models.dev ===\n")

    models_dev = fetch_models_dev()
    if not models_dev:
        print("Error: Could not fetch models")
        return None

    filtered = filter_models_by_provider(models_dev, config)

    auth = get_opencode_auth()
    enriched = enrich_with_provider_check(filtered, auth)

    free_models = [m for m in enriched if m.get("free")]
    sorted_models = sort_models(free_models)

    print(f"Found {len(sorted_models)} free models\n")

    print("=== Select a Model ===\n")

    for i, m in enumerate(sorted_models, 1):
        print(format_model_line(m, i))

    print("\n  0.  Cancel")

    while True:
        try:
            choice = input("\nEnter number: ").strip()
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(sorted_models):
                m = sorted_models[idx - 1]
                return f"{m['provider']}/{m['model_id']}"
            print(f"Invalid choice. Enter 1-{len(sorted_models)} or 0.")
        except ValueError:
            print("Enter a number.")


def manage_subagents(config: dict) -> None:
    """Manage subagent model overrides."""
    subagents = get_subagents()

    if not subagents:
        print("\nNo subagents found in .opencode/agents/")
        print("Create agents first using OpenCode.")
        return

    print("\n=== Current Subagents ===\n")
    for name, model in subagents.items():
        print(f"  {name}: {model}")

    print("\n=== Actions ===")
    print("  1. Change a subagent's model")
    print("  0. Back")

    while True:
        choice = input("\nSelect action: ").strip()

        if choice == "0":
            return

        if choice == "1":
            print("\n=== Select Subagent ===")
            for i, (name, model) in enumerate(subagents.items(), 1):
                print(f"  {i}. {name} (current: {model})")
            print("  0. Cancel")

            try:
                idx = int(input("\nEnter number: ").strip())
                if idx == 0:
                    continue
                if 1 <= idx <= len(subagents):
                    agent_name = list(subagents.keys())[idx - 1]
                    model = select_model(config)
                    if model:
                        if update_agent_model(agent_name, model):
                            print(f"\n✓ Updated {agent_name} to {model}")
                            subagents = get_subagents()
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Enter a number.")


def show_config(config: dict) -> None:
    """Display current configuration."""
    print("\n=== Current Configuration ===\n")
    print(json.dumps(config, indent=2))


def main():
    """Main entry point."""
    config_path = Path(".opencode/model-settings.jsonc")

    # Try relative to current directory, then relative to script
    if not config_path.exists():
        script_dir = Path(__file__).parent
        config_path = script_dir / ".opencode" / "model-settings.jsonc"

    config = load_jsonc(config_path)

    # Handle global flags
    min_context_override = None
    remaining_args = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--min-context" and i + 1 < len(sys.argv):
            min_context_override = int(sys.argv[i + 1])
            i += 2
        elif arg.startswith("-"):
            remaining_args.append(arg)
            i += 1
        else:
            remaining_args.append(arg)
            i += 1

    if min_context_override is not None:
        if "defaults" not in config:
            config["defaults"] = {}
        config["defaults"]["min_context_window"] = min_context_override

    sys.argv = [sys.argv[0]] + remaining_args

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd in ["-h", "--help"]:
            print("""
OpenCode Model Manager

Usage:
  python .opencode/opencode-model-manager.py [command] [options]

Commands:
  list        List available free models (sorted by benchmark)
  select     Interactively select a model for a subagent
  config     Show current configuration
  agents     Manage subagent overrides
  refresh    Show benchmark sources
  -h, --help  Show this help

Options:
  --min-context <tokens>  Override minimum context window (default: from config)

Examples:
  python .opencode/opencode-model-manager.py list
  python .opencode/opencode-model-manager.py list --min-context 100000
  python .opencode/opencode-model-manager.py agents
            """)
            return

        elif cmd == "list":
            list_models(config)
            return

        elif cmd == "config":
            show_config(config)
            return

        elif cmd in ["agents", "manage"]:
            manage_subagents(config)
            return

        elif cmd == "refresh":
            print("Benchmark scores are hardcoded for reliability.")
            print("Sources:")
            print("  - LiveCodeBench: https://llmdb.com/benchmarks/livecodebench-v5")
            print("  - SWE-Bench: https://llm-stats.com/benchmarks/swe-bench-verified")
            print("  - Vellum: https://vellum.ai/best-llm-for-coding")
            return

        else:
            print(f"Unknown command: {cmd}")
            print("Run with --help for usage.")
            sys.exit(1)

    while True:
        print("\n" + "=" * 50)
        print("OpenCode Model Manager")
        print("=" * 50)
        print("  1. List free models (by benchmark)")
        print("  2. Manage subagent models")
        print("  3. Show configuration")
        print("  0. Exit")
        print()

        choice = input("Select: ").strip()

        if choice == "1":
            list_models(config)
        elif choice == "2":
            manage_subagents(config)
        elif choice == "3":
            show_config(config)
        elif choice == "0":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
