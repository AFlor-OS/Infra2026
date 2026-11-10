from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_runtime(
    summary_csv: Path,
    output_path: Path,
    mode: str,
    title: str,
) -> None:
    df = pd.read_csv(summary_csv)

    experiment = df[df["mode"] == mode].sort_values("processes")
    baseline = df[df["mode"] == "sequential"]

    if experiment.empty or baseline.empty:
        raise ValueError(f"Dados insuficientes para o experimento {mode}")

    x = experiment["processes"].to_numpy()
    means = experiment["mean"].to_numpy()

    errors = np.vstack([
        means - experiment["ci_low"].to_numpy(),
        experiment["ci_high"].to_numpy() - means,
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.errorbar(
        x,
        means,
        yerr=errors,
        marker="o",
        capsize=5,
        label="Tempo MPI (IC 95%)",
    )

    ax.axhline(
        baseline.iloc[0]["mean"],
        linestyle="--",
        label="Baseline sequencial",
    )

    for _, row in experiment.iterrows():
        if mode == "weak":
            ax.annotate(
                f"N={int(row['n'])}",
                (row["processes"], row["mean"]),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )

    ax.set_xlabel("Número de processos")
    ax.set_ylabel("Tempo médio (s)")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_scaling(
    scaling_csv: Path,
    output_path: Path,
    mode: str,
    title: str,
) -> None:
    df = pd.read_csv(scaling_csv)
    df = df[df["mode"] == mode].sort_values("processes")

    if df.empty:
        raise ValueError(f"Dados de escalabilidade ausentes para {mode}")

    processes = df["processes"].to_numpy()
    speedup = df["speedup"].to_numpy()
    efficiency = df["efficiency"].to_numpy()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Speedup
    axes[0].plot(
        processes,
        speedup,
        marker="o",
        label="Speedup observado",
    )
    axes[0].plot(
        processes,
        processes,
        linestyle="--",
        label="Speedup ideal",
    )
    axes[0].set_xlabel("Número de processos")
    axes[0].set_ylabel("Speedup")
    axes[0].set_title("Speedup")
    axes[0].set_xticks(processes)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Efficiency
    axes[1].plot(
        processes,
        efficiency,
        marker="o",
        label="Eficiência observada",
    )
    axes[1].axhline(
        1.0,
        linestyle="--",
        label="Eficiência ideal",
    )
    axes[1].set_xlabel("Número de processos")
    axes[1].set_ylabel("Eficiência")
    axes[1].set_title("Eficiência")
    axes[1].set_xticks(processes)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def generate_campaign_plots(
    campaign_dir: Path,
    output_dir: Path,
    mode: str,
    experiment_name: str,
) -> None:
    summary_csv = campaign_dir / "summary.csv"
    scaling_csv = campaign_dir / "scaling.csv"

    if not summary_csv.exists() or not scaling_csv.exists():
        raise FileNotFoundError(f"CSV não encontrado em {campaign_dir}")

    plot_runtime(
        summary_csv,
        output_dir / f"{experiment_name}_runtime.png",
        mode,
        f"{experiment_name} - Tempo de execução",
    )

    plot_scaling(
        scaling_csv,
        output_dir / f"{experiment_name}_scaling.png",
        mode,
        f"{experiment_name} - Escalabilidade",
    )