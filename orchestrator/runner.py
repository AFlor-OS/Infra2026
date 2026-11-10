import time
import json
import os
import platform
import socket
import subprocess
import uuid

from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def get_command_output(command: list[str]) -> str | None:
    """Executa um comando e retorna sua saída, se disponível."""
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )
        return completed.stdout.strip() or completed.stderr.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def get_git_commit() -> str | None:
    """Retorna o commit Git associado à execução."""
    return get_command_output(["git", "rev-parse", "HEAD"])


def get_environment(mode: str) -> dict:
    """Coleta informações do ambiente de execução."""
    environment = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "git_commit": get_git_commit(),
    }

    if mode != "sequential":
        mpiexec = os.environ.get("MPIEXEC", "mpirun")

        environment["mpi_launcher"] = mpiexec
        environment["mpi_version"] = get_command_output(
            [mpiexec, "--version"]
        )

        environment["mpicc_version"] = get_command_output(
            ["mpicc", "--version"]
        )

    return environment


def build_command(
    mode: str,
    n: int,
    processes: int,
) -> list[str]:
    """Monta o comando de execução do workload."""
    if mode == "sequential":
        return [
            str(ROOT / "build" / "sequential"),
            str(n),
        ]

    mpiexec = os.environ.get("MPIEXEC", "mpirun")


    command = [
        mpiexec,
        "-np",
        str(processes),
        str(ROOT / "build" / "mpi_ring"),
        str(n),
    ]

    # Este ambiente possui 12 núcleos físicos e 14 threads lógicas.
    # A opção é necessária para executar P=14 sem oversubscription.
    if processes == 14:
        command.insert(1, "--use-hwthread-cpus")

    return command



def execute_command(command: list[str]) -> subprocess.CompletedProcess:
    """Executa um workload e retorna sua saída."""
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def extract_json(stdout: str) -> dict:
    """Extrai o JSON produzido pelo programa C."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()

        if line.startswith("{"):
            return json.loads(line)

    raise ValueError(
        "Nenhuma linha JSON encontrada na saída do workload."
    )


def run_one(
    mode: str,
    n: int,
    processes: int,
    repetition: int,
    warmups: int = 1,
    pause_seconds: float = 0,
    campaign_id: str | None = None,
) -> dict:
    """
    Executa um experimento, realiza warm-ups e salva
    os resultados brutos em um arquivo JSON exclusivo.
    """
    if mode not in {"sequential", "strong", "weak", "saturation"}:
        raise ValueError(f"Modo inválido: {mode}")

    if n <= 0 or processes <= 0:
        raise ValueError(
            "N e número de processos devem ser positivos."
        )

    if warmups < 0:
        raise ValueError("O número de warm-ups não pode ser negativo.")

    if mode == "sequential":
        workload_mode = "sequential"
    else:
        workload_mode = "mpi"

        if n % processes:
            raise ValueError(
                f"N={n} precisa ser divisível por P={processes}"
            )

    command = build_command(mode, n, processes)

    # Warm-up: executa o workload sem armazenar os resultados.
    for warmup_index in range(warmups):
        execute_command(command)

        if pause_seconds > 0:
            time.sleep(pause_seconds)

    if pause_seconds > 0 and warmups == 0:
        time.sleep(pause_seconds)

    completed = execute_command(command)
    payload = extract_json(completed.stdout)

    record = {
        "run_id": str(uuid.uuid4()),
        "campaign_id": campaign_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "mode": mode,
            "workload_mode": workload_mode,
            "n": n,
            "processes": processes,
            "repetition": repetition,
            "warmups": warmups,
            "pause_seconds": pause_seconds,
        },
        "environment": get_environment(mode),
        "result": payload,
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }

    RAW.mkdir(parents=True, exist_ok=True)

    path = RAW / f"{record['run_id']}.json"

    # Modo exclusivo: impede sobrescrita de resultados.
    with path.open("x", encoding="utf-8") as file:
        json.dump(record, file, indent=2, ensure_ascii=False)

    print(f"Salvo: {path.relative_to(ROOT)}")

    return record
