#define _POSIX_C_SOURCE 199309L

#include "matrix.h"
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);

if (argc < 2 || argc > 3) {
    if (rank == 0) {
        fprintf(stderr,
                "Uso: mpirun -np P %s N [--validate]\n",
                argv[0]);
    }
    MPI_Finalize();
    return 2;
}

int validate = 0;

if (argc == 3) {
    if (strcmp(argv[2], "--validate") != 0) {
        if (rank == 0) {
            fprintf(stderr, "Opcao invalida: %s\n", argv[2]);
        }
        MPI_Finalize();
        return 2;
    }

    validate = 1;
}

    char *end = NULL;
    unsigned long n_ul = strtoul(argv[1], &end, 10);
    if (!end || *end != '\0' || n_ul == 0 || n_ul % (unsigned long)p != 0) {
        if (rank == 0) fprintf(stderr, "N deve ser positivo e divisível por P\n");
        MPI_Finalize();
        return 2;
    }

    size_t n = (size_t)n_ul, rows = n / (size_t)p, local_elems = rows * n;
    double *a = malloc(local_elems * sizeof(double));
    double *b_block = malloc(local_elems * sizeof(double));
    double *c = calloc(local_elems, sizeof(double));
    double *global_c = rank == 0 ? malloc(n * n * sizeof(double)) : NULL;
    if (!a || !b_block || !c || (rank == 0 && !global_c)) {
        fprintf(stderr, "rank %d: falha de alocação\n", rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    fill_matrix_rows(a, (size_t)rank * rows, rows, n);
    fill_matrix_rows(b_block, (size_t)rank * rows, rows, n);

    MPI_Barrier(MPI_COMM_WORLD);

    double total_start = MPI_Wtime();

    double comp_seconds = 0.0;
    double mpi_seconds = 0.0;
    double gather_seconds = 0.0;

    for (int step = 0; step < p; ++step) {
        int block_id = (rank + step) % p;
        double comp_start = MPI_Wtime();
        for (size_t i = 0; i < rows; ++i) {
            for (size_t k = 0; k < rows; ++k) {
                double aik = a[i * n + (size_t)block_id * rows + k];
                for (size_t j = 0; j < n; ++j)
                    c[i * n + j] += aik * b_block[k * n + j];
            }
        }
        comp_seconds += MPI_Wtime() - comp_start;

        if (step < p - 1) {
            double mpi_start = MPI_Wtime();
            int dest = (rank - 1 + p) % p;
            int source = (rank + 1) % p;
            MPI_Sendrecv_replace(b_block, (int)local_elems, MPI_DOUBLE,
                                 dest, 100, source, 100, MPI_COMM_WORLD,
                                 MPI_STATUS_IGNORE);
            mpi_seconds += MPI_Wtime() - mpi_start;
        }
    }

    double gather_start = MPI_Wtime();

    MPI_Gather(c, (int)local_elems, MPI_DOUBLE, global_c,
            (int)local_elems, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    gather_seconds = MPI_Wtime() - gather_start;

    double total_seconds = MPI_Wtime() - total_start;

    double *rank_total = NULL;
    double *rank_compute = NULL;
    double *rank_communication = NULL;
    double *rank_gather = NULL;

    if (rank == 0) {
        rank_total = malloc(p * sizeof(double));
        rank_compute = malloc(p * sizeof(double));
        rank_communication = malloc(p * sizeof(double));
        rank_gather = malloc(p * sizeof(double));

        if (!rank_total || !rank_compute ||
            !rank_communication || !rank_gather) {
            fprintf(stderr, "Falha ao alocar tempos por processo\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
    }

    MPI_Gather(&total_seconds, 1, MPI_DOUBLE,
            rank_total, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    MPI_Gather(&comp_seconds, 1, MPI_DOUBLE,
            rank_compute, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    MPI_Gather(&mpi_seconds, 1, MPI_DOUBLE,
            rank_communication, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    MPI_Gather(&gather_seconds, 1, MPI_DOUBLE,
            rank_gather, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    double max_total = 0.0;
    double max_comp = 0.0;
    double max_mpi = 0.0;
    double max_gather = 0.0;

    if (rank == 0) {
        for (int i = 0; i < p; ++i) {
            if (rank_total[i] > max_total)
                max_total = rank_total[i];

            if (rank_compute[i] > max_comp)
                max_comp = rank_compute[i];

            if (rank_communication[i] > max_mpi)
                max_mpi = rank_communication[i];

            if (rank_gather[i] > max_gather)
                max_gather = rank_gather[i];
        }
    }
    int validation_passed = 0;
double max_relative_error = 0.0;

if (validate && rank == 0) {
    /*
     * A validacao e feita depois da medicao de desempenho.
     * Portanto, o custo da referencia sequencial nao entra
     * no tempo medido do algoritmo MPI.
     */
    double *a_ref = malloc(n * n * sizeof(double));
    double *b_ref = malloc(n * n * sizeof(double));
    double *c_ref = calloc(n * n, sizeof(double));

    if (!a_ref || !b_ref || !c_ref) {
        fprintf(stderr,
                "Falha ao alocar matrizes para validacao\n");

        free(a_ref);
        free(b_ref);
        free(c_ref);

        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    /* Reconstrui as matrizes completas de entrada. */
    fill_matrix_rows(a_ref, 0, n, n);
    fill_matrix_rows(b_ref, 0, n, n);

    /* Calcula a referencia sequencial. */
    multiply_sequential(a_ref, b_ref, c_ref, n);

    const double tolerance = 1e-10;
    validation_passed = 1;
    max_relative_error = 0.0;

    /*
     * Compara todos os N*N elementos.
     * Como os valores das matrizes deste projeto sao positivos,
     * a referencia nao deve conter elementos iguais a zero.
     */
    for (size_t i = 0; i < n * n; ++i) {
        double reference = c_ref[i];
        double actual = global_c[i];
        double absolute_error = fabs(actual - reference);

        double relative_error;

        if (reference != 0.0) {
            relative_error = absolute_error / fabs(reference);
        } else {
            relative_error = (absolute_error == 0.0) ? 0.0 : INFINITY;
        }

        if (relative_error > max_relative_error) {
            max_relative_error = relative_error;
        }

        if (relative_error > tolerance) {
            validation_passed = 0;
        }
    }

    free(a_ref);
    free(b_ref);
    free(c_ref);
}

/*
 * Todos os processos recebem o resultado da validacao.
 * Assim, o status final e consistente em todos os ranks.
 */
if (validate) {
    MPI_Bcast(&validation_passed, 1, MPI_INT, 0, MPI_COMM_WORLD);
}
    
if (rank == 0) {
    printf(
        "{\"mode\":\"mpi_ring\","
        "\"n\":%zu,"
        "\"processes\":%d,"
        "\"total_seconds_max\":%.9f,"
        "\"compute_seconds_max\":%.9f,"
        "\"communication_seconds_max\":%.9f,"
        "\"gather_seconds_max\":%.9f,"
        "\"checksum\":%.15g,"
        "\"rank_timings\":[",
        n,
        p,
        max_total,
        max_comp,
        max_mpi,
        max_gather,
        checksum(global_c, n * n)
    );

    for (int i = 0; i < p; ++i) {
        if (i > 0) printf(",");

        printf(
            "{\"rank\":%d,"
            "\"total_seconds\":%.9f,"
            "\"compute_seconds\":%.9f,"
            "\"communication_seconds\":%.9f,"
            "\"gather_seconds\":%.9f}",
            i,
            rank_total[i],
            rank_compute[i],
            rank_communication[i],
            rank_gather[i]
        );
    }

    printf("]");

    if (validate) {
        printf(
            ",\"validation_passed\":%s,"
            "\"max_relative_error\":%.15g",
            validation_passed ? "true" : "false",
            max_relative_error
        );
    }

    printf("}\n");
}

    free(a); free(b_block); free(c); free(global_c);
    int exit_code = (validate && !validation_passed) ? 1 : 0;

    free(rank_total);
    free(rank_compute);
    free(rank_communication);
    free(rank_gather);

    MPI_Finalize();
    return exit_code;
}
