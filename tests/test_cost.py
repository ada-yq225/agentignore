import pytest
from agentignore.cost import estimate_dollar_cost


def test_explicit_price_full_read_scenario():
    assert estimate_dollar_cost(10_000, 100, input_rate=3) == 3


@pytest.mark.parametrize('rate', [-1, float('nan'), float('inf')])
def test_invalid_price_rejected(rate):
    with pytest.raises(ValueError):
        estimate_dollar_cost(100, input_rate=rate)
