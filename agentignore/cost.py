"""Explicit hypothetical scenarios; no provider prices or measured-savings claims."""
import math


def estimate_dollar_cost(tokens: int, queries: int = 100, *, input_rate: float) -> float:
    if tokens < 0 or queries < 1 or not math.isfinite(input_rate) or input_rate < 0:
        raise ValueError('tokens and rate must be nonnegative; queries must be positive')
    return tokens * queries * input_rate / 1_000_000
