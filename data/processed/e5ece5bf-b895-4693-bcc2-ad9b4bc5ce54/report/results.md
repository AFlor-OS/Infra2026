# E2 - Escalabilidade forte

## 1. Tempos de execução

| Configuração | N | Processos | Média (s) | Desvio (s) | CV | IC 95% |
|---|---:|---:|---:|---:|---:|---:|
| Sequencial | 4960 | 1 | 84.5988 | 0.4290 | 0.51% | [84.2919, 84.9057] |
| MPI | 4960 | 1 | 85.3250 | 1.0315 | 1.21% | [84.5872, 86.0629] |
| MPI | 4960 | 2 | 41.6630 | 1.7767 | 4.26% | [40.3920, 42.9340] |
| MPI | 4960 | 4 | 41.2772 | 1.1622 | 2.82% | [40.4459, 42.1086] |
| MPI | 4960 | 8 | 67.7711 | 5.2523 | 7.75% | [64.0138, 71.5283] |

## 2. Speedup e eficiência

| N | Processos | Speedup | Eficiência |
|---:|---:|---:|---:|
| 4960 | 1 | 0.9915 | 99.15% |
| 4960 | 2 | 2.0306 | 101.53% |
| 4960 | 4 | 2.0495 | 51.24% |
| 4960 | 8 | 1.2483 | 15.60% |

## 3. Destaques dos resultados

- Menor tempo médio paralelo: **41.2772 s**, com 4 processos e matriz N=4960.
- Maior speedup observado: **2.0495**, com 4 processos.

## 4. Observações metodológicas

- Os tempos apresentados correspondem às médias das execuções.
- Os intervalos de confiança de 95% referem-se às médias dos tempos.
- Speedup e eficiência são apresentados como estimativas pontuais.
- Os intervalos de confiança de speedup e eficiência não foram calculados nesta configuração.
