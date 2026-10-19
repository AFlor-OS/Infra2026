# MPI Scaling Lab

Projeto acadêmico para estudar strong scaling e weak scaling com multiplicação densa de matrizes, C, Open MPI e análise em Python.

## Requisitos locais

- Linux ou macOS com compilador C (`gcc`/`clang`)
- Open MPI (`mpicc`, `mpirun`)
- Python 3.10+
- `make`

No macOS, instale ferramentas com Homebrew, por exemplo: `brew install open-mpi gcc make`.
No Ubuntu/Debian: `sudo apt install build-essential openmpi-bin libopenmpi-dev python3-venv`.

> O relatório usa Ubuntu 24.04, GCC 13 e Open MPI 4.1.x no ambiente final. Em desenvolvimento local, registre as versões reais. O desempenho em um laptop não substitui medições nas VMs do LaSDPC.

## Começar

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
make all
make smoke
```

Se o Open MPI recusar execução como root em Linux, não execute os experimentos como root. A opção `--allow-run-as-root` não deve ser usada como padrão.

## Executar manualmente

```bash
./build/sequential 256
mpirun -np 2 ./build/mpi_ring 256
```

O tamanho `N` deve ser divisível pelo número de processos. O programa MPI imprime uma linha JSON com tempos e checksum.

## Executar pelo orquestrador

```bash
python -m orchestrator.cli run --mode strong --n 256 --processes 1 2 4 --repetitions 3
python -m orchestrator.cli analyze
```

Os arquivos brutos são gravados em `data/raw/` com nomes únicos e não são sobrescritos. Não use tamanhos grandes antes do piloto: o custo da multiplicação é O(N³) e a memória cresce com N².

## Próximos incrementos

1. Validar checksum MPI contra o sequencial.
2. Implementar kernel bloqueado com bloco 64 e medições de computação por processo.
3. Adicionar PMPI (`LD_PRELOAD`) e métricas de sistema.
4. Completar cenários E0–E7 e estatística bootstrap/IC95%.
5. Integrar FastAPI, Prometheus, Pushgateway, Node Exporter e Grafana.
6. Adaptar execução a múltiplas VMs via SSH.

O scaffold inicial não implementa ainda todos os requisitos de instrumentação do relatório; veja `docs/architecture.md`.
