# Arquitetura e limitações do scaffold

A versão inicial implementa multiplicação de matrizes com decomposição 1-D por linhas e circulação em anel do bloco de linhas de B. A matriz A local mantém as colunas globais, e cada passo usa o bloco B correspondente para acumular as contribuições em C.

O baseline sequencial e a versão MPI usam a mesma fórmula determinística para gerar A e B e o mesmo checksum simples. O checksum é útil como verificação inicial, mas não substitui uma comparação elemento a elemento com tolerância relativa de 1e-10, que deve ser adicionada antes da campanha definitiva.

A versão inicial registra o tempo total da região paralela e os tempos agregados de computação e chamadas MPI no stdout. Ainda faltam: várias amostras internas, aquecimento descartado, PMPI completo interceptando chamadas, métricas de CPU/RSS/rede, comparação de checksum automatizada, modelo de custo ajustado, cenários E0-E7, bootstrap para métricas derivadas, interface web completa e integração Prometheus/Grafana.

O MPI é executado no host, não em contêiner, para evitar que a rede virtual de contêineres altere as medições. Docker Compose ficará reservado para os serviços de controle/observabilidade.
