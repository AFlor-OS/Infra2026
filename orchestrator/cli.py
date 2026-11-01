
import argparse
from pathlib import Path

import yaml

from .compiler import compile_targets
from .runner import run_one
from .calibration import calibrate
from orchestrator.campaigns import create_campaign, finish_campaign
from analysis.metrics import summarize_raw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "experiments.yaml"

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def load_config(path: Path) -> dict:
    """Carrega a configuração dos experimentos."""
    with path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuração YAML inválida.")

    return config


def execute_repetitions(
    mode: str,
    n: int,
    processes: int,
    repetitions: int,
    warmups: int,
    pause_seconds: float,
    campaign_id: str,
):
    """Executa uma configuração experimental repetidas vezes."""
    for repetition in range(1, repetitions + 1):
        print(
            f"\n[{mode}] N={n}, P={processes}, "
            f"repetição={repetition}/{repetitions}"
        )

        run_one(
            mode=mode,
            n=n,
            processes=processes,
            repetition=repetition,
            warmups=warmups,
            pause_seconds=pause_seconds,
            campaign_id=campaign_id,
        )


def run_campaign(config: dict, campaign_id: str):
    """Executa todos os experimentos habilitados no YAML."""
    execution = config["execution"]
    experiments = config["experiments"]

    warmups = int(execution["warmups"])
    pause_seconds = float(execution["pause_seconds"])

    compile_targets()

    # -------------------------------------------------
    # Escalabilidade forte (E2)
    # -------------------------------------------------
    strong = experiments.get("strong", {})

    if strong.get("enabled", False):
        n = int(strong["matrix_size"])
        processes_list = strong["processes"]
        repetitions = int(strong["repetitions"])

        print("\n=== ESCALABILIDADE FORTE ===")

        execute_repetitions(
            mode="sequential",
            n=n,
            processes=1,
            repetitions=repetitions,
            warmups=warmups,
            pause_seconds=pause_seconds,
            campaign_id=campaign_id,
        )

        for processes in processes_list:
            execute_repetitions(
                mode="strong",
                n=n,
                processes=int(processes),
                repetitions=repetitions,
                warmups=warmups,
                pause_seconds=pause_seconds,
                campaign_id=campaign_id,
            )

    # -------------------------------------------------
    # Escalabilidade fraca (E3)
    # -------------------------------------------------
    weak = experiments.get("weak", {})

    if weak.get("enabled", False):
        base_n = int(weak["base_matrix_size"])
        processes_list = weak["processes"]
        matrix_sizes = weak["matrix_sizes"]
        repetitions = int(weak["repetitions"])

        if len(processes_list) != len(matrix_sizes):
            raise ValueError(
                "weak.processes e weak.matrix_sizes "
                "precisam ter o mesmo tamanho."
            )

        print("\n=== ESCALABILIDADE FRACA ===")

        execute_repetitions(
            mode="sequential",
            n=base_n,
            processes=1,
            repetitions=repetitions,
            warmups=warmups,
            pause_seconds=pause_seconds,
            campaign_id=campaign_id,
        )

        for processes, n in zip(processes_list, matrix_sizes):
            execute_repetitions(
                mode="weak",
                n=int(n),
                processes=int(processes),
                repetitions=repetitions,
                warmups=warmups,
                pause_seconds=pause_seconds,
                campaign_id=campaign_id,
            )

    # -------------------------------------------------
    # Saturação (E4)
    # -------------------------------------------------
    saturation = experiments.get("saturation", {})

    if saturation.get("enabled", False):
        matrix_sizes = saturation["matrix_sizes"]
        processes_list = saturation["processes"]
        repetitions = int(saturation["repetitions"])

        print("\n=== SATURAÇÃO ===")

        for n in matrix_sizes:
            for processes in processes_list:
                execute_repetitions(
                    mode="saturation",
                    n=int(n),
                    processes=int(processes),
                    repetitions=repetitions,
                    warmups=warmups,
                    pause_seconds=pause_seconds,
                    campaign_id=campaign_id,
                )

    print("\nCampanha finalizada.")


def main():
    parser = argparse.ArgumentParser(
        description="MPI Scaling Lab"
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # -------------------------------------------------
    # Comando RUN
    # -------------------------------------------------
    run = sub.add_parser(
        "run",
        help="Executa a campanha definida no YAML",
    )

    run.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
    )

    # -------------------------------------------------
    # Comando ANALYZE
    # -------------------------------------------------
    analyze = sub.add_parser(
        "analyze",
        help="Analisa os resultados brutos",
    )

    analyze.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
    )

    analyze.add_argument(
        "--campaign-id",
        type=str,
        default=None,
        help="Analisa somente os resultados desta campanha.",
    )

    # -------------------------------------------------
    # Comando CALIBRATE
    # -------------------------------------------------
    calibration = sub.add_parser(
        "calibrate",
        help="Calibra automaticamente o tamanho da matriz",
    )

    calibration.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
    )

    # -------------------------------------------------
    # Processamento dos argumentos
    # -------------------------------------------------
    args = parser.parse_args()

    # -------------------------------------------------
    # EXECUÇÃO DA CAMPANHA
    # -------------------------------------------------
    if args.command == "run":
        config = load_config(args.config)
        campaign_id = create_campaign(config)

        try:
            run_campaign(config, campaign_id)

        except Exception as error:
            finish_campaign(
                campaign_id,
                status="failed",
                error=str(error),
            )
            raise

        else:
            finish_campaign(
                campaign_id,
                status="completed",
            )

    # -------------------------------------------------
    # ANÁLISE DOS RESULTADOS
    # -------------------------------------------------
    elif args.command == "analyze":
        config = load_config(args.config)

        if args.campaign_id:
            output_dir = PROCESSED / args.campaign_id
        else:
            output_dir = PROCESSED

        output = summarize_raw(
            raw_dir=RAW,
            output_dir=output_dir,
            statistics_config=config["statistics"],
            experiment_config=config,
            campaign_id=args.campaign_id,
        )

        print(f"\nResultados gerados em: {output_dir}")
        print(f"Arquivo principal: {output}")

    # -------------------------------------------------
    # CALIBRAÇÃO AUTOMÁTICA
    # -------------------------------------------------
    elif args.command == "calibrate":
        config = load_config(args.config)
        campaign_id = create_campaign(config)

        try:
            compile_targets()
            calibrate(config, campaign_id)

        except Exception as error:
            finish_campaign(
                campaign_id,
                status="failed",
                error=str(error),
            )
            raise

        else:
            finish_campaign(
                campaign_id,
                status="completed",
            )


if __name__ == "__main__":
    main()
