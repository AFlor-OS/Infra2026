from pathlib import Path

import pandas as pd


def format_seconds(value):
    if pd.isna(value):
        return "—"
    return f"{value:.4f}"


def format_percentage(value):
    if pd.isna(value):
        return "—"
    return f"{value * 100:.2f}%"


def generate_report(campaign_dir: Path) -> Path:
    """
    Gera tabelas e resumo em Markdown a partir dos CSVs
    produzidos pelo módulo de métricas.
    """
    summary_path = campaign_dir / "summary.csv"
    scaling_path = campaign_dir / "scaling.csv"

    if not summary_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {summary_path}")

    if not scaling_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {scaling_path}")

    summary = pd.read_csv(summary_path)
    scaling = pd.read_csv(scaling_path)

    output_dir = campaign_dir / "report"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Identifica o experimento da campanha.
    modes = summary.loc[
        summary["mode"].isin(["strong", "weak"]), "mode"
    ].unique()

    if len(modes) != 1:
        raise ValueError(
            f"Esperado um único experimento por campanha. Encontrados: {modes}"
        )

    mode = modes[0]
    experiment_name = "E2 - Escalabilidade forte" if mode == "strong" else (
        "E3 - Escalabilidade fraca"
    )

    # Salva tabelas completas em CSV.
    summary.to_csv(output_dir / "runtime_table.csv", index=False)
    scaling.to_csv(output_dir / "scaling_table.csv", index=False)

    # Separa baseline e execuções paralelas.
    baseline = summary[summary["mode"] == "sequential"]
    parallel = summary[summary["mode"] == mode].sort_values("processes")

    if baseline.empty or parallel.empty:
        raise ValueError("Baseline ou resultados paralelos não encontrados.")

    # Monta o relatório Markdown.
    lines = [
        f"# {experiment_name}",
        "",
        "## 1. Tempos de execução",
        "",
        "| Configuração | N | Processos | Média (s) | Desvio (s) | CV | IC 95% |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in baseline.iterrows():
        ci = (
            f"[{row['ci_low']:.4f}, {row['ci_high']:.4f}]"
            if pd.notna(row.get("ci_low")) and pd.notna(row.get("ci_high"))
            else "—"
        )
        lines.append(
            f"| Sequencial | {int(row['n'])} | 1 | "
            f"{format_seconds(row['mean'])} | "
            f"{format_seconds(row['std'])} | "
            f"{format_percentage(row['cv'])} | {ci} |"
        )

    for _, row in parallel.iterrows():
        ci = (
            f"[{row['ci_low']:.4f}, {row['ci_high']:.4f}]"
            if pd.notna(row.get("ci_low")) and pd.notna(row.get("ci_high"))
            else "—"
        )
        lines.append(
            f"| MPI | {int(row['n'])} | {int(row['processes'])} | "
            f"{format_seconds(row['mean'])} | "
            f"{format_seconds(row['std'])} | "
            f"{format_percentage(row['cv'])} | {ci} |"
        )

    lines.extend([
        "",
        "## 2. Speedup e eficiência",
        "",
        "| N | Processos | Speedup | Eficiência |",
        "|---:|---:|---:|---:|",
    ])

    for _, row in scaling.sort_values("processes").iterrows():
        lines.append(
            f"| {int(row['n'])} | {int(row['processes'])} | "
            f"{row['speedup']:.4f} | "
            f"{format_percentage(row['efficiency'])} |"
        )

    # Identifica os melhores resultados observados.
    best_runtime = parallel.loc[parallel["mean"].idxmin()]
    best_speedup = scaling.loc[scaling["speedup"].idxmax()]

    lines.extend([
        "",
        "## 3. Destaques dos resultados",
        "",
        (
            f"- Menor tempo médio paralelo: **{best_runtime['mean']:.4f} s**, "
            f"com {int(best_runtime['processes'])} processos "
            f"e matriz N={int(best_runtime['n'])}."
        ),
        (
            f"- Maior speedup observado: **{best_speedup['speedup']:.4f}**, "
            f"com {int(best_speedup['processes'])} processos."
        ),
        "",
        "## 4. Observações metodológicas",
        "",
        "- Os tempos apresentados correspondem às médias das execuções.",
        "- Os intervalos de confiança de 95% referem-se às médias dos tempos.",
        "- Speedup e eficiência são apresentados como estimativas pontuais.",
        "- Os intervalos de confiança de speedup e eficiência não foram "
        "calculados nesta configuração.",
    ])

    if mode == "weak":
        lines.extend([
            "- Na escalabilidade fraca, a eficiência considera o crescimento "
            "do tamanho do problema em relação à quantidade de processos, "
            "conforme a fórmula implementada no módulo de métricas."
        ])

    report_path = output_dir / "results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Relatório gerado em: {output_dir}")
    print(f"- {output_dir / 'runtime_table.csv'}")
    print(f"- {output_dir / 'scaling_table.csv'}")
    print(f"- {report_path}")

    return output_dir