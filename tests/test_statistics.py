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


from analysis.statistics import bootstrap_ratio_ci


def test_bootstrap_ratio_ci_has_expected_fields():
    result = bootstrap_ratio_ci(
        [10, 11, 12, 13, 14],
        [5, 5, 6, 6, 7],
        samples=5000,
        seed=2026,
    )

    assert "bootstrap_ci_low" in result
    assert "bootstrap_ci_high" in result
    assert result["bootstrap_ci_low"] < 2.0
    assert result["bootstrap_ci_high"] > 2.0


def test_bootstrap_ratio_ci_is_reproducible():
    numerator = [10, 11, 12, 13, 14]
    denominator = [5, 6, 7, 8, 9]

    first = bootstrap_ratio_ci(
        numerator, denominator, samples=1000, seed=42
    )
    second = bootstrap_ratio_ci(
        numerator, denominator, samples=1000, seed=42
    )

    assert first == second


def test_bootstrap_ratio_ci_rejects_invalid_denominator():
    with pytest.raises(ValueError):
        bootstrap_ratio_ci([10, 11], [0, 2])


def test_bootstrap_ratio_ci_requires_repetitions():
    with pytest.raises(ValueError):
        bootstrap_ratio_ci([10], [5, 6])
