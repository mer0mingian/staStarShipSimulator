---
description: "Fetch and display free programming models from OpenRouter with >128k context window"
disable-model-invocation: false
---
# Get OpenRouter Free Models

This command queries the OpenRouter API to retrieve all free models tagged with "Programming" that have a context window larger than 128k tokens.

## Implementation

```python
import os
import json
import urllib.request
import urllib.error
import re

def get_free_programming_models() -> str:
    """
    Fetch free programming models from OpenRouter with >128k context.

    Returns:
        Formatted table of models or error message
    """
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "❌ Error: OPENROUTER_API_KEY environment variable is not set"

    # Prepare request
    url = "https://openrouter.ai/api/v1/models?category=programming"

    try:
        # Make API request
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {api_key}")

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        models_list = data.get("data", [])

        if not models_list:
            return "⚠️  No models returned from OpenRouter API"

        # Filter for free models with >128k context
        filtered_models = []
        for model in models_list:
            # Check if model is free (prompt and completion pricing both 0)
            pricing = model.get("pricing", {})
            prompt_price = pricing.get("prompt", float('inf'))
            completion_price = pricing.get("completion", float('inf'))

            # Extract prompt price if it's a dict or string
            if isinstance(prompt_price, dict):
                prompt_price = float(prompt_price.get("price", float('inf')))
            elif isinstance(prompt_price, str):
                try:
                    prompt_price = float(prompt_price)
                except (ValueError, TypeError):
                    prompt_price = float('inf')
            else:
                prompt_price = float(prompt_price) if prompt_price is not None else float('inf')

            # Extract completion price if it's a dict or string
            if isinstance(completion_price, dict):
                completion_price = float(completion_price.get("price", float('inf')))
            elif isinstance(completion_price, str):
                try:
                    completion_price = float(completion_price)
                except (ValueError, TypeError):
                    completion_price = float('inf')
            else:
                completion_price = float(completion_price) if completion_price is not None else float('inf')

            # Check context length
            context_length = model.get("context_length", 0)
            if context_length is None:
                context_length = 0

            # Filter: free and >128k context
            if prompt_price == 0 and completion_price == 0 and context_length > 128000:
                filtered_models.append({
                    "id": model.get("id", "N/A"),
                    "name": model.get("name", "N/A"),
                    "context_length": context_length,
                    "model_data": model
                })

        if not filtered_models:
            return "⚠️  No free programming models found with >128k context window"

        # Sort by context length descending
        filtered_models.sort(key=lambda x: x["context_length"], reverse=True)

        # Format as table
        table_lines = [
            "# Free Programming Models (>128k context)",
            "",
            "| OpenCode Model String | Model Name | Context Size | Daily Limit | Programming Rank |",
            "|----------------------|------------|--------------|-------------|------------------|"
        ]

        for model in filtered_models:
            model_id = model["id"]
            # Create OpenCode connection string format: openrouter/model-id
            opencode_model = f"openrouter/{model_id}"
            name = model["name"][:35] + "..." if len(model["name"]) > 35 else model["name"]
            context = f"{model['context_length']:,}"

            # Try to extract daily limit info (may not be available in API)
            daily_limit = "N/A"
            model_data = model["model_data"]
            per_request_limits = model_data.get("per_request_limits", {})
            if per_request_limits:
                prompt_limit = per_request_limits.get("prompt_tokens")
                completion_limit = per_request_limits.get("completion_tokens")
                if prompt_limit or completion_limit:
                    daily_limit = f"P:{prompt_limit or 'N/A'} C:{completion_limit or 'N/A'}"

            # Try to extract programming rank (may not be directly available)
            prog_rank = "N/A"
            description = model_data.get("description", "")
            if "Programming" in description:
                # Check if there's a rank mentioned like "(#48)"
                rank_match = re.search(r'Programming \(#(\d+)\)', description)
                if rank_match:
                    prog_rank = f"#{rank_match.group(1)}"

            table_lines.append(
                f"| {opencode_model} | {name} | {context} | {daily_limit} | {prog_rank} |"
            )

        table_lines.append("")
        table_lines.append(f"**Total models found:** {len(filtered_models)}")

        return "\n".join(table_lines)

    except urllib.error.HTTPError as e:
        return f"❌ Error: HTTP {e.code} - {e.reason}\nFailed to fetch data from OpenRouter API"
    except urllib.error.URLError as e:
        return f"❌ Error: Network error\nReason: {e.reason}"
    except TimeoutError:
        return "❌ Error: Request to OpenRouter API timed out"
    except json.JSONDecodeError:
        return "❌ Error: Invalid JSON response from OpenRouter API"
    except Exception as e:
        return f"❌ Error: Unexpected error occurred\nReason: {str(e)}"

# Execute the function
result = get_free_programming_models()
print(result)
```

## Usage

Simply invoke the command:

```
/get-free-models
```

## Output Format

The command returns a markdown table with the following columns:

- **OpenCode Model String**: The connection string to use in OpenCode config (format: `openrouter/model-id`)
- **Model Name**: The display name of the model
- **Context Size**: Maximum context window in tokens
- **Daily Limit**: Per-request token limits (if available) shown as "P:prompt_tokens C:completion_tokens"
- **Programming Rank**: Ranking for programming tasks on OpenRouter (if available)

### Example Usage in OpenCode

To use one of these models in OpenCode, add it to your `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openrouter": {
      "models": {
        "model-name-from-api": {
          "name": "Display Name"
        }
      }
    }
  },
  "model": "openrouter/model-name-from-api"
}
```

Or use it directly with the model string shown in the table (e.g., `openrouter/qwen/qwen-3-coder-480b-a35b:free`)

## Error Handling

The command handles the following error cases:

- **Missing API Key**: Returns clear error if `OPENROUTER_API_KEY` is not set
- **API Request Failure**: Returns error with HTTP status code
- **Timeout**: Returns timeout error if request takes too long
- **Empty Results**: Returns message if no models match the criteria
- **Unexpected Errors**: Returns generic error message with details
