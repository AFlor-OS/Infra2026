from scipy import stats
import numpy as np

def mean_ci95(values):
    values = np.asarray(values, dtype=float)
    if values.size < 2:
        raise ValueError("São necessárias pelo menos duas observações")
    mean = float(values.mean())
    sem = stats.sem(values)
    low, high = stats.t.interval(0.95, df=values.size - 1, loc=mean, scale=sem)
    return {"n": int(values.size), "mean": mean, "std": float(values.std(ddof=1)),
            "ci95_low": float(low), "ci95_high": float(high)}
