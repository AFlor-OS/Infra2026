#include "matrix.h"
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);

    if (argc != 2) {
        if (rank == 0) fprintf(stderr, "Uso: mpirun -np P %s N\n", argv[0]);
        MPI_Finalize();
        return 2;
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
    double comp_seconds = 0.0, mpi_seconds = 0.0;

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
    double total_seconds = MPI_Wtime() - total_start;

    MPI_Gather(c, (int)local_elems, MPI_DOUBLE, global_c,
               (int)local_elems, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    double max_total = 0.0, max_comp = 0.0, max_mpi = 0.0;
    MPI_Reduce(&total_seconds, &max_total, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&comp_seconds, &max_comp, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&mpi_seconds, &max_mpi, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("{\"mode\":\"mpi_ring\",\"n\":%zu,\"processes\":%d,"
               "\"total_seconds\":%.9f,\"compute_seconds_max\":%.9f,"
               "\"mpi_seconds_max\":%.9f,\"checksum\":%.15g}\n",
               n, p, max_total, max_comp, max_mpi, checksum(global_c, n * n));
    }
    free(a); free(b_block); free(c); free(global_c);
    MPI_Finalize();
    return 0;
}
