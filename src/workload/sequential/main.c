#define _POSIX_C_SOURCE 199309L

#include "matrix.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Uso: %s N\n", argv[0]);
        return 2;
    }
    char *end = NULL;
    unsigned long n_ul = strtoul(argv[1], &end, 10);
    if (!end || *end != '\0' || n_ul == 0) {
        fprintf(stderr, "N deve ser inteiro positivo\n");
        return 2;
    }
    size_t n = (size_t)n_ul;
    if (n > 10000) {
        fprintf(stderr, "N muito grande para esta versão inicial\n");
        return 2;
    }

    double *a = malloc(n * n * sizeof(double));
    double *b = malloc(n * n * sizeof(double));
    double *c = calloc(n * n, sizeof(double));
    if (!a || !b || !c) {
        fprintf(stderr, "Falha ao alocar matrizes\n");
        free(a); free(b); free(c);
        return 1;
    }
    fill_matrix_rows(a, 0, n, n);
    fill_matrix_rows(b, 0, n, n);

    struct timespec start, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start);
    multiply_sequential(a, b, c, n);
    clock_gettime(CLOCK_MONOTONIC, &end_time);
    double elapsed = (end_time.tv_sec - start.tv_sec) +
                     (end_time.tv_nsec - start.tv_nsec) / 1e9;
    printf("{\"mode\":\"sequential\",\"n\":%zu,\"processes\":1,"
           "\"total_seconds\":%.9f,\"checksum\":%.15g}\n",
           n, elapsed, checksum(c, n * n));
    free(a); free(b); free(c);
    return 0;
}
