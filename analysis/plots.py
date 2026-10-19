from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def plot_runtime(csv_path: Path, output_path: Path) -> None:
    df = pd.read_csv(csv_path)
    if "processes" not in df or "total_seconds" not in df:
        raise ValueError("CSV não contém colunas de tempo e processos")
    summary = df.groupby("processes")["total_seconds"].mean().sort_index()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.plot(summary.index, summary.values, marker="o")
    plt.xlabel("Número de processos")
    plt.ylabel("Tempo total (s)")
    plt.title("Tempo médio por número de processos")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
