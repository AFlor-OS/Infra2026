#include "matrix.h"

/* Fórmula determinística: não depende de rand() nem de comunicação. */
double matrix_value(size_t row, size_t col) {
    return (double)(((row * 17u + col * 13u + 7u) % 101u) + 1u) / 101.0;
}

void fill_matrix_rows(double *matrix, size_t first_global_row, size_t rows, size_t n) {
    for (size_t i = 0; i < rows; ++i)
        for (size_t j = 0; j < n; ++j)
            matrix[i * n + j] = matrix_value(first_global_row + i, j);
}

void multiply_sequential(const double *a, const double *b, double *c, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        for (size_t k = 0; k < n; ++k) {
            const double aik = a[i * n + k];
            for (size_t j = 0; j < n; ++j)
                c[i * n + j] += aik * b[k * n + j];
        }
    }
}

double checksum(const double *matrix, size_t elements) {
    double sum = 0.0;
    for (size_t i = 0; i < elements; ++i) sum += matrix[i];
    return sum;
}
