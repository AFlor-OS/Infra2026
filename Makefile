CC = gcc
MPICC = mpicc
CFLAGS = -O3 -march=native -Wall -Wextra -std=c11
BUILD = build

.PHONY: all clean smoke
all: $(BUILD)/sequential $(BUILD)/mpi_ring

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/sequential: src/workload/sequential/main.c src/workload/common/matrix.c src/workload/common/matrix.h | $(BUILD)
	$(CC) $(CFLAGS) -Isrc/workload/common src/workload/sequential/main.c src/workload/common/matrix.c -o $@

$(BUILD)/mpi_ring: src/workload/mpi/main.c src/workload/common/matrix.c src/workload/common/matrix.h | $(BUILD)
	$(MPICC) $(CFLAGS) -Isrc/workload/common src/workload/mpi/main.c src/workload/common/matrix.c -o $@

smoke: all
	./$(BUILD)/sequential 64
	mpirun -np 2 ./$(BUILD)/mpi_ring 64

clean:
	rm -f $(BUILD)/sequential $(BUILD)/mpi_ring
