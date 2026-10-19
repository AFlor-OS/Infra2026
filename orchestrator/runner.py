import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

def run_one(mode: str, n: int, processes: int, repetition: int) -> dict:
    if mode not in {"sequential", "strong", "weak"}:
        raise ValueError(f"Modo inválido: {mode}")
    if n <= 0 or processes <= 0:
        raise ValueError("N e número de processos devem ser positivos")

    if mode == "sequential":
        command = [str(ROOT / "build" / "sequential"), str(n)]
    else:
        if n % processes:
            raise ValueError(f"N={n} precisa ser divisível por P={processes}")
        mpiexec = os.environ.get("MPIEXEC", "mpirun")
        command = [mpiexec, "-np", str(processes),
                   str(ROOT / "build" / "mpi_ring"), str(n)]

    completed = subprocess.run(command, cwd=ROOT, text=True,
                               capture_output=True, check=True)
    # O programa imprime uma única linha JSON no stdout.
    result_line = next(line for line in reversed(completed.stdout.splitlines())
                       if line.strip().startswith("{"))
    payload = json.loads(result_line)
    record = {
        "run_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config": {"mode": mode, "n": n, "processes": processes,
                   "repetition": repetition},
        "result": payload,
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{record['run_id']}.json"
    # Modo exclusivo: não sobrescreve dados brutos.
    with path.open("x", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    print(f"Salvo: {path.relative_to(ROOT)}")
    return record
