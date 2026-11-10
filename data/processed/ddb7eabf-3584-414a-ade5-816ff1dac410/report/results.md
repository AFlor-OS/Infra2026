# E3 - Escalabilidade fraca

## 1. Tempos de execução

| Configuração | N | Processos | Média (s) | Desvio (s) | CV | IC 95% |
|---|---:|---:|---:|---:|---:|---:|
| Sequencial | 2048 | 1 | 6.6830 | 0.0668 | 1.00% | [6.6351, 6.7308] |
| MPI | 2048 | 1 | 6.7236 | 0.0765 | 1.14% | [6.6688, 6.7784] |
| MPI | 2584 | 2 | 5.9604 | 0.2126 | 3.57% | [5.8083, 6.1124] |
| MPI | 3248 | 4 | 11.9769 | 0.5714 | 4.77% | [11.5682, 12.3856] |
| MPI | 4096 | 8 | 38.2472 | 3.7301 | 9.75% | [35.5789, 40.9155] |

## 2. Speedup e eficiência

| N | Processos | Speedup | Eficiência |
|---:|---:|---:|---:|
| 2048 | 1 | 0.9940 | 99.40% |
| 2584 | 2 | 1.1212 | 112.60% |
| 3248 | 4 | 0.5580 | 55.64% |
| 4096 | 8 | 0.1747 | 17.47% |

## 3. Destaques dos resultados

- Menor tempo médio paralelo: **5.9604 s**, com 2 processos e matriz N=2584.
- Maior speedup observado: **1.1212**, com 2 processos.

## 4. Observações metodológicas

- Os tempos apresentados correspondem às médias das execuções.
- Os intervalos de confiança de 95% referem-se às médias dos tempos.
- Speedup e eficiência são apresentados como estimativas pontuais.
- Os intervalos de confiança de speedup e eficiência não foram calculados nesta configuração.
- Na escalabilidade fraca, a eficiência considera o crescimento do tamanho do problema em relação à quantidade de processos, conforme a fórmula implementada no módulo de métricas.
