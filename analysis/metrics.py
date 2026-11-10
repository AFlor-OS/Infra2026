
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.statistics import (
    describe,
    mean_ci,
    bootstrap_ci,
    bootstrap_ratio_ci,
)


def get_runtime(result: dict) -> float:
    """Obtém o tempo total da execução."""
    candidates = [
        "total_seconds_max",
        "total_seconds",
        "runtime_seconds",
    ]

    for key in candidates:
        if key in result:
            value = float(result[key])

            if value <= 0:
                raise ValueError(f"Tempo inválido: {key}={value}")

            return value

    raise ValueError(
        "Resultado não possui um campo de tempo total reconhecido."
    )


def load_raw_runs(
    raw_dir: Path,
    campaign_id: str | None = None,
) -> list[dict]:
    """Carrega os arquivos JSON de resultados brutos."""
    rows = []

    for path in sorted(raw_dir.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            item = json.load(file)

        item_campaign_id = item.get("campaign_id")

        if campaign_id is not None and item_campaign_id != campaign_id:
            continue

        config = item["config"]
        result = item["result"]

        row = {
            **config,
            "run_id": item["run_id"],
            "campaign_id": item_campaign_id,
            "timestamp_utc": item.get("timestamp_utc"),
                        "runtime_seconds": get_runtime(result),
            "compute_seconds": result.get("compute_seconds_max"),
            "communication_seconds": result.get("communication_seconds_max"),
            "gather_seconds": result.get("gather_seconds_max"),
            "communication_fraction": (
                result["communication_seconds_max"] / get_runtime(result)
                if result.get("communication_seconds_max") is not None
                else None
            ),
            "gather_fraction": (
                result["gather_seconds_max"] / get_runtime(result)
                if result.get("gather_seconds_max") is not None
                else None
            ),
            "checksum": result.get("checksum"),
            "validation_passed": result.get("validation_passed"),
            "max_relative_error": result.get("max_relative_error"),
            "rank_timings": json.dumps(
                result.get("rank_timings", []),
                ensure_ascii=False,
            ),
        }

        rows.append(row)

    return rows



def summarize_raw(
    raw_dir: Path,
    output_dir: Path,
    statistics_config: dict | None = None,
    experiment_config: dict | None = None,
    campaign_id: str | None = None,
) -> Path:
    """
    Gera runs.csv, summary.csv e scaling.csv.
    Calcula escalabilidade somente quando existe baseline compatível.
    """
    statistics_config = statistics_config or {}
    experiment_config = experiment_config or {}

    confidence_level = float(
        statistics_config.get("confidence_level", 0.95)
    )

    bootstrap_config = statistics_config.get("bootstrap", {})
    bootstrap_enabled = bootstrap_config.get("enabled", True)
    bootstrap_samples = int(bootstrap_config.get("samples", 10000))
    bootstrap_confidence = float(
        bootstrap_config.get("confidence_level", confidence_level)
    )

    seed = int(
        experiment_config.get("execution", {}).get(
            "random_seed", 2026
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_raw_runs(
    raw_dir,
    campaign_id=campaign_id,
)

    if not rows:
        if campaign_id:
            raise ValueError(
                f"Nenhuma execução encontrada para a campanha {campaign_id}"
            )

        raise ValueError(
            f"Nenhum resultado JSON encontrado em {raw_dir}"
        )

    runs = pd.DataFrame(rows)

    runs.to_csv(output_dir / "runs.csv", index=False)

    # Estatísticas descritivas
    group_columns = ["mode", "n", "processes"]
    summary_rows = []

    for key, group in runs.groupby(group_columns):
        values = group["runtime_seconds"].to_numpy(dtype=float)

        stats_result = describe(values)

        component_metrics = {
            "compute_seconds": "compute_mean_seconds",
            "communication_seconds": "communication_mean_seconds",
            "gather_seconds": "gather_mean_seconds",
            "communication_fraction": "communication_fraction_mean",
            "gather_fraction": "gather_fraction_mean",
        }

        for source_column, output_column in component_metrics.items():
            if source_column in group:
                component_values = (
                    group[source_column].dropna().to_numpy(dtype=float)
                )

                if component_values.size:
                    stats_result[output_column] = float(
                        np.mean(component_values)
                    )

        if len(values) >= 2:
            stats_result.update(mean_ci(values, confidence_level))

            if bootstrap_enabled:
                stats_result.update(
                    bootstrap_ci(
                        values,
                        confidence_level=bootstrap_confidence,
                        samples=bootstrap_samples,
                        seed=seed,
                    )
                )

        mode, n, processes = key

        summary_rows.append({
            **stats_result,
            "mode": mode,
            "n": int(n),
            "processes": int(processes),
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output_dir / "summary.csv", index=False)

    # Escalabilidade
    scaling_rows = []


    sequential = runs[runs["mode"] == "sequential"]

    for _, row in summary.iterrows():
        mode = row["mode"]

        if mode not in {"strong", "weak", "saturation"}:
            continue

        n = int(row["n"])
        processes = int(row["processes"])

        # P=1 é o próprio baseline no experimento de saturação.
        # Não precisamos calcular speedup de uma configuração contra ela mesma.
        if mode == "saturation" and processes == 1:
            continue

        parallel_values = runs[
            (runs["mode"] == mode)
            & (runs["n"] == n)
            & (runs["processes"] == processes)
        ]["runtime_seconds"].to_numpy(dtype=float)

        if mode == "saturation":
            baseline_n = n

            baseline_values = runs[
                (runs["mode"] == "saturation")
                & (runs["n"] == n)
                & (runs["processes"] == 1)
            ]["runtime_seconds"].to_numpy(dtype=float)

            efficiency_factor = 1.0 / processes

        else:
            if mode == "strong":
                baseline_n = n
                efficiency_factor = 1.0 / processes
            else:
                baseline_n = int(
                    experiment_config.get("experiments", {})
                    .get("weak", {})
                    .get("base_matrix_size", 2048)
                )
                efficiency_factor = (n / baseline_n) ** 3 / processes

            baseline_values = sequential[
                sequential["n"] == baseline_n
            ]["runtime_seconds"].to_numpy(dtype=float)

        # Sem baseline, não é possível calcular speedup.
        if baseline_values.size == 0:
            print(
                f"[AVISO] Sem baseline compatível para N={baseline_n}. "
                f"Ignorando {mode}, N={n}, P={processes}."
            )
            continue

        if parallel_values.size == 0:
            continue

        baseline_mean = float(np.mean(baseline_values))
        parallel_mean = float(np.mean(parallel_values))

        speedup_value = baseline_mean / parallel_mean
        efficiency_value = speedup_value * efficiency_factor

        result = {
            "mode": mode,
            "n": n,
            "processes": processes,
            "baseline_n": baseline_n,
            "baseline_repetitions": int(baseline_values.size),
            "parallel_repetitions": int(parallel_values.size),
            "baseline_mean_seconds": baseline_mean,
            "parallel_mean_seconds": parallel_mean,
            "speedup": speedup_value,
            "efficiency": efficiency_value,
        }

        if (
            bootstrap_enabled
            and baseline_values.size >= 2
            and parallel_values.size >= 2
        ):
            ratio_ci = bootstrap_ratio_ci(
                baseline_values,
                parallel_values,
                confidence_level=bootstrap_confidence,
                samples=bootstrap_samples,
                seed=seed,
            )

            result["speedup_ci_low"] = ratio_ci["bootstrap_ci_low"]
            result["speedup_ci_high"] = ratio_ci["bootstrap_ci_high"]

            result["efficiency_ci_low"] = (
                ratio_ci["bootstrap_ci_low"] * efficiency_factor
            )
            result["efficiency_ci_high"] = (
                ratio_ci["bootstrap_ci_high"] * efficiency_factor
            )

        scaling_rows.append(result)

    scaling_columns = [
        "mode",
        "n",
        "processes",
        "baseline_n",
        "baseline_repetitions",
        "parallel_repetitions",
        "baseline_mean_seconds",
        "parallel_mean_seconds",
        "speedup",
        "efficiency",
        "speedup_ci_low",
        "speedup_ci_high",
        "efficiency_ci_low",
        "efficiency_ci_high",
    ]

    scaling = pd.DataFrame(scaling_rows, columns=scaling_columns)
    scaling.to_csv(output_dir / "scaling.csv", index=False)

    if campaign_id:
        print(f"Campanha analisada: {campaign_id}")
    else:
        print("Análise realizada com todas as campanhas disponíveis.")

    print(f"Execuções: {output_dir / 'runs.csv'}")
    print(f"Estatísticas: {output_dir / 'summary.csv'}")
    print(f"Escalabilidade: {output_dir / 'scaling.csv'}")

    if scaling.empty:
        print("[AVISO] Nenhuma configuração possui baseline compatível.")
    else:
        print(f"Configurações de escalabilidade calculadas: {len(scaling)}")

    return output_dir / "runs.csv"


def speedup(
    sequential_seconds: float,
    parallel_seconds: float,
) -> float:
    if parallel_seconds <= 0:
        raise ValueError("O tempo paralelo deve ser positivo")

    return sequential_seconds / parallel_seconds


def efficiency(speedup_value: float, processes: int) -> float:
    if processes <= 0:
        raise ValueError("O número de processos deve ser positivo")

    return speedup_value / processes
