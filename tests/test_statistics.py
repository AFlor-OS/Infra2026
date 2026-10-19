import pytest
from analysis.statistics import mean_ci95

def test_ci_has_expected_fields():
    result = mean_ci95([1, 2, 3, 4, 5])
    assert result["n"] == 5
    assert result["mean"] == 3.0
    assert result["ci95_low"] < result["mean"] < result["ci95_high"]

def test_requires_repetitions():
    with pytest.raises(ValueError):
        mean_ci95([1])
