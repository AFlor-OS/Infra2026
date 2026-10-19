import json
from pathlib import Path
import pandas as pd

def summarize_raw(raw_dir: Path, output_dir: Path) -> Path:
    rows = []
    for path in sorted(raw_dir.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            item = json.load(f)
        row = {**item["config"], **item["result"], "run_id": item["run_id"]}
        rows.append(row)
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "runs.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out

def speedup(sequential_seconds: float, parallel_seconds: float) -> float:
    if parallel_seconds <= 0:
        raise ValueError("O tempo paralelo deve ser positivo")
    return sequential_seconds / parallel_seconds

def efficiency(speedup_value: float, processes: int) -> float:
    if processes <= 0:
        raise ValueError("O número de processos deve ser positivo")
    return speedup_value / processes
