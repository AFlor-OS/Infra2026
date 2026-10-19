#!/usr/bin/env python3
"""Piloto deliberadamente pequeno; use N baixo antes de calibrar o workload."""
from orchestrator.compiler import compile_targets
from orchestrator.runner import run_one

if __name__ == "__main__":
    compile_targets()
    for p in (1, 2, 4):
        run_one("strong", n=128, processes=p, repetition=1)
