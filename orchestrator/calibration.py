
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.runner import run_one

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_DIR = ROOT / "data" / "processed" / "calibration"


def round_matrix_size(value: float, multiple: int = 8) -> int:
    """Arredonda N para o múltiplo definido mais próximo."""
    return max(multiple, int(round(value / multiple)) * multiple)


def estimate_next_size(n: int, elapsed: float, target: float) -> int:
    """Estima um novo N usando a relação aproximada T proporcional a N³."""
    if elapsed <= 0:
        raise ValueError("O tempo medido precisa ser positivo.")

    factor = (target / elapsed) ** (1 / 3)

    # Limita a mudança para evitar saltos excessivos.
    factor = max(0.5, min(2.0, factor))

    return round_matrix_size(n * factor)


def execute_trial(
    n: int,
    repetition: int,
    warmups: int,
    pause_seconds: float,
    campaign_id: str,
) -> dict:
    """Executa uma medição sequencial e retorna seus dados."""
    record = run_one(
        mode="sequential",
        n=n,
        processes=1,
        repetition=repetition,
        warmups=warmups,
        pause_seconds=pause_seconds,
        campaign_id=campaign_id,
    )

    elapsed = float(record["result"]["total_seconds"])

    print(f"N={n}: {elapsed:.3f} segundos")

    return {
        "n": n,
        "repetition": repetition,
        "elapsed_seconds": elapsed,
        "run_id": record["run_id"],
    }


def calibrate(config: dict, campaign_id: str) -> dict:
    """Encontra e confirma um tamanho de matriz para escalabilidade forte."""
    settings = config.get("calibration", {})

    target_min = float(settings.get("target_min_seconds", 60))
    target_max = float(settings.get("target_max_seconds", 120))
    target = float(settings.get("target_seconds", 90))

    start_n = int(settings.get("start_matrix_size", 512))
    max_n = int(settings.get("max_matrix_size", 4096))
    max_attempts = int(settings.get("max_search_attempts", 8))
    confirmation_repetitions = int(
        config["statistics"].get("pilot_repetitions", 3)
    )

    execution = config["execution"]
    warmups = int(execution["warmups"])
    pause_seconds = float(execution["pause_seconds"])

    if not (0 < target_min <= target <= target_max):
        raise ValueError(
            "A faixa de calibração precisa satisfazer "
            "0 < mínimo <= alvo <= máximo."
        )

    if start_n <= 0 or max_n < start_n:
        raise ValueError("Tamanhos inicial e máximo inválidos.")

    calibration_id = str(uuid.uuid4())
    trials = []
    n = round_matrix_size(start_n)

    print("\n=== CALIBRAÇÃO AUTOMÁTICA ===")
    print(f"Faixa desejada: {target_min:.1f}–{target_max:.1f} s")
    print(f"Tempo-alvo: {target:.1f} s")
    print(f"Tamanho inicial: N={n}")
    print(f"Tamanho máximo: N={max_n}")

    selected_n = None

    # Busca adaptativa: uma medição por tamanho.
    for attempt in range(1, max_attempts + 1):
        if n > max_n:
            n = max_n

        print(f"\nBusca {attempt}/{max_attempts}")

        trial = execute_trial(
            n=n,
            repetition=attempt,
            warmups=warmups,
            pause_seconds=pause_seconds,
            campaign_id=campaign_id,
        )
        trials.append(trial)

        elapsed = trial["elapsed_seconds"]

        if target_min <= elapsed <= target_max:
            selected_n = n
            break

        if n == max_n and elapsed < target_min:
            break

        next_n = estimate_next_size(n, elapsed, target)

        if next_n == n:
            break

        n = min(next_n, max_n)

    if selected_n is None:
        raise RuntimeError(
            "Não foi encontrado um tamanho de matriz dentro da faixa "
            f"de {target_min:.1f} a {target_max:.1f} segundos. "
            "Aumente max_matrix_size ou ajuste os parâmetros "
            "de calibração."
        )

        print(
            "\nNão foi possível encontrar um tamanho dentro da faixa "
            "na busca inicial. Será feita a confirmação do melhor candidato."
        )

    # Confirmação: executa repetições adicionais no tamanho selecionado.
    print(f"\n=== CONFIRMAÇÃO: N={selected_n} ===")

    confirmation = []

    for repetition in range(1, confirmation_repetitions + 1):
        trial = execute_trial(
            n=selected_n,
            repetition=repetition,
            warmups=warmups,
            pause_seconds=pause_seconds,
            campaign_id=campaign_id,
        )
        confirmation.append(trial)

    times = [item["elapsed_seconds"] for item in confirmation]
    mean_seconds = sum(times) / len(times)

    result = {
        "calibration_id": calibration_id,
        "campaign_id": campaign_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": {
            "minimum_seconds": target_min,
            "maximum_seconds": target_max,
            "target_seconds": target,
        },
        "selected_matrix_size": selected_n,
        "confirmation_repetitions": len(confirmation),
        "confirmation_times_seconds": times,
        "mean_seconds": mean_seconds,
        "within_target": target_min <= mean_seconds <= target_max,
        "search_trials": trials,
        "confirmation_trials": confirmation,
        "warmups": warmups,
        "pause_seconds": pause_seconds,
    }

    output_dir = CALIBRATION_DIR / calibration_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "calibration.json"

    with output_file.open("x", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    print("\n=== RESULTADO DA CALIBRAÇÃO ===")
    print(f"Tamanho selecionado: N={selected_n}")
    print(f"Tempo médio de confirmação: {mean_seconds:.3f} s")
    print(f"Dentro da faixa: {'sim' if result['within_target'] else 'não'}")
    print(f"Resultado salvo em: {output_file.relative_to(ROOT)}")

    return result
