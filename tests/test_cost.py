"""Tests for token cost and monetary impact calculator."""

from agentignore.cost import estimate_dollar_cost, get_all_model_costs


def test_estimate_dollar_cost():
    # 1,000,000 tokens for 1 query at $3.00/1M = $3.00
    cost = estimate_dollar_cost(1_000_000, queries=1, model_name="Claude 3.5 / 3.7 Sonnet")
    assert cost == 3.00

    # 10,000 tokens per query for 100 queries = 1,000,000 total tokens = $3.00
    cost_100 = estimate_dollar_cost(10_000, queries=100, model_name="Claude 3.5 / 3.7 Sonnet")
    assert cost_100 == 3.00


def test_get_all_model_costs():
    costs = get_all_model_costs(10_000, queries=100)
    assert "Claude 3.5 / 3.7 Sonnet" in costs
    assert "GPT-4o" in costs
    assert costs["Claude 3.5 / 3.7 Sonnet"] == 3.00
    assert costs["GPT-4o"] == 2.50
