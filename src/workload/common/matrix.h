#ifndef MATRIX_H
#define MATRIX_H
#include <stddef.h>

double matrix_value(size_t row, size_t col);
void fill_matrix_rows(double *matrix, size_t first_global_row, size_t rows, size_t n);
void multiply_sequential(const double *a, const double *b, double *c, size_t n);
double checksum(const double *matrix, size_t elements);

#endif
