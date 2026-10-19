from pathlib import Path
from fastapi import FastAPI
import json

app = FastAPI(title="MPI Scaling Lab", version="0.1.0")
ROOT = Path(__file__).resolve().parents[1]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/runs")
def list_runs():
    raw = ROOT / "data" / "raw"
    runs = []
    for path in sorted(raw.glob("*.json"), reverse=True):
        try:
            runs.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return {"count": len(runs), "runs": runs[:100]}
