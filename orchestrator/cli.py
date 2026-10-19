import argparse
import json
from pathlib import Path
from .compiler import compile_targets
from .runner import run_one
from analysis.metrics import summarize_raw

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description="MPI Scaling Lab")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Executa uma campanha pequena")
    run.add_argument("--mode", choices=["sequential", "strong", "weak"], default="strong")
    run.add_argument("--n", type=int, required=True)
    run.add_argument("--processes", type=int, nargs="+", default=[1, 2, 4])
    run.add_argument("--repetitions", type=int, default=3)
    sub.add_parser("analyze", help="Agrega JSONs brutos em CSV")
    args = parser.parse_args()

    if args.command == "run":
        compile_targets()
        for p in args.processes:
            for rep in range(1, args.repetitions + 1):
                run_one("sequential" if args.mode == "sequential" else args.mode,
                        args.n, 1 if args.mode == "sequential" else p, rep)
    elif args.command == "analyze":
        output = summarize_raw(ROOT / "data" / "raw", ROOT / "data" / "processed")
        print(f"CSV gerado: {output}")

if __name__ == "__main__":
    main()
