"""Cost calculator to estimate monetary impact of token waste across major LLM providers."""

from typing import Dict

# Pricing per 1,000,000 input tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "Claude 3.5 / 3.7 Sonnet": {"rate": 3.00, "provider": "Anthropic"},
    "GPT-4o": {"rate": 2.50, "provider": "OpenAI"},
    "Claude 3 Opus": {"rate": 15.00, "provider": "Anthropic"},
    "GPT-4o-mini": {"rate": 0.15, "provider": "OpenAI"},
    "Gemini 1.5 Pro": {"rate": 1.25, "provider": "Google"},
}

DEFAULT_BENCHMARK_MODEL = "Claude 3.5 / 3.7 Sonnet"


def estimate_dollar_cost(tokens: int, queries: int = 100, model_name: str = DEFAULT_BENCHMARK_MODEL) -> float:
    """Calculate the estimated USD cost of burning `tokens` for `queries` requests."""
    rate = MODEL_PRICING.get(model_name, {}).get("rate", 3.00)
    total_tokens = tokens * queries
    return (total_tokens / 1_000_000) * rate


def get_all_model_costs(tokens: int, queries: int = 100) -> Dict[str, float]:
    """Calculate waste across all major model providers."""
    results: Dict[str, float] = {}
    for model, info in MODEL_PRICING.items():
        rate = info["rate"]
        total_tokens = tokens * queries
        results[model] = (total_tokens / 1_000_000) * rate
    return results
