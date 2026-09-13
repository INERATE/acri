import pytest

from acri import Tool, index, resolve


@pytest.mark.parametrize("k", [-1, True, 1.5, "5"])
def test_invalid_limits_fail_before_returning_tools(k):
    with pytest.raises(ValueError, match="non-negative integer"):
        resolve("weather", index([Tool("weather", "weather")]), k=k)


def test_zero_limit_offers_no_ranked_tools():
    assert resolve("weather", index([Tool("weather", "weather")]), k=0) == []
