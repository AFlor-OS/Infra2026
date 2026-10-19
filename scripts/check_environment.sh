#!/usr/bin/env bash
set -euo pipefail
for cmd in gcc mpicc mpirun make python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Comando ausente: $cmd" >&2
    exit 1
  fi
  printf '%-8s %s\n' "$cmd" "$(command -v "$cmd")"
done
mpicc --version | head -n 1
mpirun --version | head -n 1
python3 --version
