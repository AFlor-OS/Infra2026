import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def compile_targets() -> None:
    if not shutil.which("gcc") and not shutil.which("cc"):
        raise RuntimeError("Compilador C não encontrado.")
    if not shutil.which("mpicc"):
        raise RuntimeError("mpicc não encontrado. Instale Open MPI.")
    subprocess.run(["make", "all"], cwd=ROOT, check=True)
