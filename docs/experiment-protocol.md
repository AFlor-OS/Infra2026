# Protocolo inicial

1. Registre compilador, MPI, CPU, memória e sistema operacional.
2. Rode primeiro N=64 ou N=128 e confirme a execução.
3. Compare a checksum sequencial e MPI; automatize a comparação antes de usar resultados cientificamente.
4. Faça um piloto para calibrar N e evitar execução longa demais.
5. Use pelo menos cinco execuções independentes por configuração no primeiro relatório preliminar.
6. Preserve cada JSON bruto; não edite manualmente os arquivos.
7. Não compare resultados obtidos com diferentes flags, kernels, bindings ou versões de MPI sem registrar a diferença.
