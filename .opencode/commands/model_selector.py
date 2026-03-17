import os
import json
import urllib.request
import urllib.error
import re
import sys
import argparse
from typing import List, Dict, Optional, Any

# --- Mock Data ---
MOCK_OPENROUTER_MODELS = [
    {
        "id": "openrouter/gpt-4o",
        "name": "GPT-4o",
        "description": "OpenAI GPT-4o model. Best for general reasoning and coding. Programming rank (#1).",
        "context_length": 128000,
        "pricing": {"prompt": 5.00, "completion": 15.00},
        "supported_parameters": ["tools", "reasoning"],
        "reasoning": {"effort": "high"}
    },
    {
        "id": "openrouter/claude-opus-4-6",
        "name": "Claude Opus 4.6",
        "description": "Anthropic Claude Opus model. Excellent for complex reasoning and long context. Programming rank (#2).",
        "context_length": 200000,
        "pricing": {"prompt": 15.00, "completion": 75.00},
        "supported_parameters": ["tools", "reasoning"],
        "reasoning": {"effort": "xhigh"}
    },
    {
        "id": "openrouter/gemini-3.1-pro-preview",
        "name": "Gemini 3.1 Pro Preview",
        "description": "Google Gemini Pro model. Good for coding and reasoning tasks. Programming rank (#3).",
        "context_length": 1000000,
        "pricing": {"prompt": 0.50, "completion": 1.50},
        "supported_parameters": ["tools", "reasoning"],
        "reasoning": {"effort": "high"}
    },
    {
        "id": "openrouter/minimax-m2.5-free",
        "name": "MiniMax M2.5 Free",
        "description": "MiniMax M2.5 model. Free tier available. Programming rank (#4).",
        "context_length": 131072,
        "pricing": {"prompt": 0, "completion": 0},
        "supported_parameters": ["tools"],
        "reasoning": {"effort": "medium"}
    },
    {
        "id": "openrouter/qwen3-coder-480b-a35b-instruct",
        "name": "Qwen3 Coder 480B",
        "description": "Qwen3 Coder model. Optimized for coding tasks. Programming rank (#5).",
        "context_length": 480000,
        "pricing": {"prompt": 0, "completion": 0},
        "supported_parameters": ["tools"],
        "reasoning": {"effort": "high"}
    },
    {
        "id": "openrouter/gpt-5-nano",
        "name": "GPT-5 Nano",
        "description": "A small, fast model. Good for quick tasks.",
        "context_length": 16000,
        "pricing": {"prompt": 0, "completion": 0},
        "supported_parameters": [],
        "reasoning": {"effort": "minimal"}
    },
    {
        "id": "openrouter/no-tools-no-reasoning-free",
        "name": "No Tools, No Reasoning Free",
        "description": "A free model, but lacks tool/reasoning support.",
        "context_length": 150000,
        "pricing": {"prompt": 0, "completion": 0},
        "supported_parameters": [],
        "reasoning": {"effort": "minimal"}
    },
    {
        "id": "openrouter/expensive-no-reasoning",
        "name": "Expensive, No Reasoning",
        "description": "Expensive model without reasoning.",
        "context_length": 200000,
        "pricing": {"prompt": 10.00, "completion": 20.00},
        "supported_parameters": [],
        "reasoning": {"effort": "none"}
    }
]

MOCK_OPENSCODE_ZEN_MODELS = {
    "minimax-m2.1-free": {
        "id": "opencode/minimax-m2.1-free",
        "name": "OpenCode Zen MiniMax M2.1 Free",
        "context_length": 131072,
        "tool_support": True,
        "reasoning_effort": "high"
    },
    "gpt-5-nano": {
        "id": "opencode/gpt-5-nano",
        "name": "OpenCode Zen GPT-5 Nano",
        "context_length": 16000,
        "tool_support": False,
        "reasoning_effort": "minimal"
    }
}

def get_openrouter_models(min_context_size: int, blacklist: List[str]) -> tuple[Optional[Dict], Optional[Dict]]:
    filtered_models = []
    try:
        models_list = MOCK_OPENROUTER_MODELS

        for model in models_list:
            if model.get("id") in blacklist:
                continue

            pricing = model.get("pricing", {})
            prompt_price = pricing.get("prompt", float('inf'))
            completion_price = pricing.get("completion", float('inf'))
            if prompt_price != 0 or completion_price != 0:
                continue

            context_length = model.get("context_length", 0) or 0
            if context_length < min_context_size:
                continue

            if "tools" not in model.get("supported_parameters", []):
                continue

            reasoning_effort = model.get("reasoning", {"effort": "none"}).get("effort", "none")
            if reasoning_effort in ["minimal", "none"]:
                continue

            filtered_models.append({
                "id": model.get("id", "N/A"),
                "name": model.get("name", "N/A"),
                "context_length": context_length,
                "reasoning_effort": reasoning_effort,
                "description": model.get("description", "")
            })

        if not filtered_models:
            print("⚠️ No suitable OpenRouter models found after filtering.", file=sys.stderr)
            return None, None

        def sort_key(m):
            rank = float('inf')
            description = m.get("description", "")
            rank_match = re.search(r'Programming rank \(#(\d+)\)', description)
            if rank_match:
                rank = int(rank_match.group(1))
            return (rank, -m.get("context_length", 0))

        filtered_models.sort(key=sort_key)

        best_model = filtered_models[0]
        best_small_model = None

        for m in filtered_models:
            if m.get("context_length", 0) < 50000:
                best_small_model = m
                break

        if not best_small_model and best_model:
            best_small_model = best_model

        return best_model, best_small_model

    except Exception as e:
        print(f"❌ Error: Unexpected error during OpenRouter model fetch/filter\nReason: {str(e)}", file=sys.stderr)
        return None, None

def get_fallback_models() -> tuple[Optional[Dict], Optional[Dict]]:
    fallback_default_model = MOCK_OPENSCODE_ZEN_MODELS.get("minimax-m2.1-free")
    fallback_small_model = MOCK_OPENSCODE_ZEN_MODELS.get("gpt-5-nano")

    return fallback_default_model, fallback_small_model

def create_dynamic_config_content(best_model: Optional[Dict], best_small_model: Optional[Dict], excluded_agents: List[str]) -> str:
    config = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {},
        "model": None,
        "small_model": None,
        "agent": {}
    }

    if best_model:
        config["model"] = best_model.get("id")
    if best_small_model:
        config["small_model"] = best_small_model.get("id")

    agent_configs = {}
    if best_model:
        AGENTS_TO_CONFIGURE = [
            "architect", "code-auditor", "code-reviewer", "data-engineer",
            "explore", "general", "python-dev"
        ]

        for agent_name in AGENTS_TO_CONFIGURE:
            if agent_name not in excluded_agents:
                agent_configs[agent_name] = {"model": best_model.get("id")}

    if agent_configs:
        config["agent"] = agent_configs

    return json.dumps(config, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select OpenRouter models for OpenCode.")
    parser.add_argument("--min-context-size", type=int, default=128000, help="Minimum context size for models.")
    parser.add_argument("--blacklist-models", nargs='*', default=[], help="List of OpenRouter model IDs to exclude.")
    parser.add_argument("--exclude-agents", nargs='*', default=["build", "plan", "orchestrator"], help="List of agents to exclude from model override.")
    parser.add_argument("--output-config", action="store_true", help="Output the dynamic OpenCode config JSON.")
    parser.add_argument("--output-export", action="store_true", help="Output the shell command to export the config.")
    parser.add_argument("--output-script", action="store_true", help="Output a wrapper script to run OpenCode.")

    args = parser.parse_args()

    best_openrouter_model, best_openrouter_small_model = get_openrouter_models(args.min_context_size, args.blacklist_models)

    if best_openrouter_model is None or best_openrouter_small_model is None:
        sys.stderr.write("--- Using Fallback Models ---\n")
        best_model, best_small_model = get_fallback_models()
    else:
        best_model = best_openrouter_model
        best_small_model = best_openrouter_small_model

        if best_small_model is None and best_model:
            best_small_model = best_model

    sys.stderr.write("--- Selected Models ---\n")
    if best_model:
        sys.stderr.write(f"Default Model: {best_model.get('id')} ({best_model.get('name')}, Context: {best_model.get('context_length'):,}, Reasoning: {best_model.get('reasoning_effort')})\n")
    else:
        sys.stderr.write("Default Model: Not selected (fallback failed)\n")

    if best_small_model:
        sys.stderr.write(f"Default Small Model: {best_small_model.get('id')} ({best_small_model.get('name')}, Context: {best_small_model.get('context_length'):,})\n")
    else:
        sys.stderr.write("Default Small Model: Not selected (fallback failed)\n")

    dynamic_config_content_json = create_dynamic_config_content(best_model, best_small_model, args.exclude_agents)

    if args.output_config:
        print(dynamic_config_content_json)
    elif args.output_export:
        escaped_json = json.dumps(dynamic_config_content_json)
        print(f"export OPENCODE_CONFIG_CONTENT={escaped_json}")
    elif args.output_script:
        # Construct the wrapper script content. Ensure proper quoting and escaping.
        # The `\` before quotes and special characters are crucial for bash interpretation.
        script_content = f"#!/bin/bash\n\n# Wrapper script for OpenCode with dynamic model selection\n\n# Default parameters (used if not provided via arguments to the wrapper script)\nDEFAULT_MIN_CONTEXT_SIZE=128000\nDEFAULT_BLACKLIST_MODELS=\"\" # Empty string for no blacklist by default\nDEFAULT_EXCLUDED_AGENTS=\"build plan orchestrator\"\n\n# Parse arguments passed to the wrapper script (these will be passed to the python script)\nMIN_CONTEXT_SIZE=${{MIN_CONTEXT_SIZE:-${{DEFAULT_MIN_CONTEXT_SIZE}}}}\nBLACKLIST_MODELS=${{BLACKLIST_MODELS:-${{DEFAULT_BLACKLIST_MODELS}}}}\nEXCLUDED_AGENTS=${{EXCLUDED_AGENTS:-${{DEFAULT_EXCLUDED_AGENTS}}}}\n\n# Path to the Python script\nPYTHON_SCRIPT_PATH=\"/home/mer0/repositories/staStarShipSimulator/.opencode/commands/model_selector.py\"\n\n# Construct the command to run the python script with its arguments\n# Use careful quoting for arguments that might contain spaces or special characters.\n# The python script outputs JSON to stdout when --output-config is used.\n# stderr of the python script is preserved by default unless explicitly redirected.\nPYTHON_CMD=\"python3 \"{PYTHON_SCRIPT_PATH}\" \
    --min-context-size \"${{MIN_CONTEXT_SIZE}}\" \
    --blacklist-models ${{BLACKLIST_MODELS}} \
    --exclude-agents \"{EXCLUDED_AGENTS}\" \
    --output-config\"\n\n# Execute the Python script to get the config JSON\n# Redirecting stderr of python script to /dev/null to keep stdout clean for JSON capture, but this might hide useful errors.\n# A better approach is to capture both stdout and stderr and process them if needed, but for now, we focus on stdout for JSON.\nCONFIG_JSON=$(\${{PYTHON_CMD}} 2>/dev/null)\n\n# Check if the python script returned valid JSON config\nif [ -z "$CONFIG_JSON" ] || ! echo "$CONFIG_JSON" | grep -q '"model":'; then
    echo "❌ Error: Failed to generate OpenCode config. Launching OpenCode without dynamic configuration." >&2
    exec opencode \"$@\"
else
    # Export the config content and launch opencode\n    export OPENCODE_CONFIG_CONTENT="$CONFIG_JSON"
    echo "LAUNCHING OPEnCODE with OPENCODE_CONFIG_CONTENT set..." >&2
    # Launch opencode with the original arguments passed to the wrapper script\n    exec opencode \"$@\"
fi\n"
        print(script_content)
    else:
        print(dynamic_config_content_json)
