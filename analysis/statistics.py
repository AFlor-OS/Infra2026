
import numpy as np
from scipy import stats


def describe(values):
    """Estatísticas descritivas de uma amostra."""
    values = np.asarray(values, dtype=float)

    if values.size == 0:
        raise ValueError("A amostra não pode estar vazia.")

    mean = float(np.mean(values))
    median = float(np.median(values))
    std = float(np.std(values, ddof=1)) if values.size >= 2 else 0.0

    q1, q3 = np.percentile(values, [25, 75])

    cv = std / mean if mean != 0 else None

    return {
        "n": int(values.size),
        "mean": mean,
        "std": std,
        "median": median,
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "cv": float(cv) if cv is not None else None,
    }


def mean_ci(values, confidence_level=0.95):
    """Intervalo de confiança t de Student para a média."""
    values = np.asarray(values, dtype=float)

    if values.size < 2:
        raise ValueError(
            "São necessárias pelo menos duas observações."
        )

    mean = float(np.mean(values))
    sem = stats.sem(values)

    low, high = stats.t.interval(
        confidence_level,
        df=values.size - 1,
        loc=mean,
        scale=sem,
    )

    return {
        "ci_low": float(low),
        "ci_high": float(high),
        "ci_half_width": float((high - low) / 2),
    }


def mean_ci95(values):
    """Compatibilidade com a função anterior."""
    result = describe(values)
    result.update(mean_ci(values, 0.95))

    result["ci95_low"] = result.pop("ci_low")
    result["ci95_high"] = result.pop("ci_high")

    return result


def bootstrap_ci(
    values,
    confidence_level=0.95,
    samples=10000,
    seed=2026,
):
    """IC bootstrap percentil para a média."""
    values = np.asarray(values, dtype=float)

    if values.size < 2:
        raise ValueError(
            "São necessárias pelo menos duas observações."
        )

    rng = np.random.default_rng(seed)

    indices = rng.integers(
        0,
        values.size,
        size=(samples, values.size),
    )

    bootstrap_means = values[indices].mean(axis=1)

    alpha = 1.0 - confidence_level

    low, high = np.quantile(
        bootstrap_means,
        [alpha / 2, 1 - alpha / 2],
    )

    return {
        "bootstrap_ci_low": float(low),
        "bootstrap_ci_high": float(high),
    }


def bootstrap_ratio_ci(
    numerator,
    denominator,
    confidence_level=0.95,
    samples=10000,
    seed=2026,
):
    """IC bootstrap para a razão entre duas médias independentes."""
    numerator = np.asarray(numerator, dtype=float)
    denominator = np.asarray(denominator, dtype=float)

    if numerator.size < 2 or denominator.size < 2:
        raise ValueError(
            "Cada amostra precisa ter pelo menos duas observações."
        )

    if np.any(denominator <= 0):
        raise ValueError("Os denominadores devem ser positivos.")

    rng = np.random.default_rng(seed)

    numerator_indices = rng.integers(
        0, numerator.size, size=(samples, numerator.size)
    )
    denominator_indices = rng.integers(
        0, denominator.size, size=(samples, denominator.size)
    )

    numerator_means = numerator[numerator_indices].mean(axis=1)
    denominator_means = denominator[denominator_indices].mean(axis=1)

    ratios = numerator_means / denominator_means

    alpha = 1.0 - confidence_level

    low, high = np.quantile(
        ratios,
        [alpha / 2, 1 - alpha / 2],
    )

    return {
        "bootstrap_ci_low": float(low),
        "bootstrap_ci_high": float(high),
    }
