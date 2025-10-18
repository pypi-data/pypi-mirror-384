////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/PPMMUtils.hpp"

#include <cmath>
#include <iostream>
#include <vector>

using u128 = unsigned __int128;
using i128 = __int128;

// Matrix multiplication functions on CPU (matrices are stored in row-major)
inline void matrix_multiply_row_major(const double *A, const double *B,
                                      double *C, int M, int N, int K) {
    // A: M x K, B: K x N, C: M x N
    // All matrices are stored as row-major
    for (int col = 0; col < N; ++col) {
        for (int row = 0; row < M; ++row) {
            double sum = 0.0;
            for (int i = 0; i < K; ++i) {
                sum += A[row * K + i] * B[i * N + col];
            }
            C[row * N + col] = sum;
        }
    }
}

// Matrix multiplication functions on CPU (matrices are stored in column-major)
inline void matrix_multiply_column_major(const double *A, const double *B,
                                         double *C, int M, int N, int K) {
    // A: M x K, B: K x N, C: M x N
    // All matrices are stored as column-major
    for (int col = 0; col < N; ++col) {
        for (int row = 0; row < M; ++row) {
            double sum = 0.0;
            for (int i = 0; i < K; ++i) {
                sum += A[row + i * M] * B[i + col * K];
            }
            C[row + col * M] = sum;
        }
    }
}

// Matrix multiplication functions on CPU (matrices are stored in column-major)
inline void matrix_row_multiply_column(const double *A, const double *B,
                                       double *C, int M, int N, int K) {
    // A: M x K, B: K x N, C: M x N
    // A: row-major B: column-major C: column-major
    for (int row = 0; row < M; ++row) {
        for (int col = 0; col < N; ++col) {
            double sum = 0.0;
            for (int i = 0; i < K; ++i) {
                sum += A[i + row * K] * B[i + col * K];
            }
            C[row + col * M] = sum;
        }
    }
}

// Result comparison function (compares matrices stored in column-major)
inline void compare_matrices(const double *A, const double *B, int size,
                             double tolerance) {
    double max_diff = 0.0;
    int max_index = 0;
    for (int i = 0; i < size; ++i) {
        double diff = fabs(A[i] - B[i]);
        if (diff > max_diff) {
            max_diff = diff;
            max_index = i;
        }
        if (diff > tolerance) {
            // If it exceeds the tolerance, it continues to find the maximum
            // error.
            // return false;
        }
    }
    std::cout << "Maximum error: " << max_diff << " (index: " << max_index
              << ")\n";
    if (max_diff > tolerance) {
        std::cout << "\033[1m\033[31m"
                  << "Results don't match.\n"
                  << "\033[0m";
    } else {
        std::cout << "\033[1m\033[32m"
                  << "The results match.\n"
                  << "\033[0m";
    }
}

// Compare result function (compares i64 matrices stored in column-major)
inline void compare_matrices_int(const hem::i64 *A, const hem::i64 *B, int size,
                                 hem::i64 tolerance = 0) {
    hem::i64 max_diff = 0;
    int max_index = 0;

    for (int i = 0; i < size; ++i) {
        hem::i64 diff = std::abs(A[i] - B[i]);
        if (diff > max_diff) {
            max_diff = diff;
            max_index = i;
        }
        if (diff > tolerance) {
            // If it exceeds the tolerance, it continues to find the maximum
            // error.
            // return false;
        }
    }
    std::cout << "** Matrix Multiplication Results " << std::endl;
    std::cout << "Maximum error: " << max_diff << " (index: " << max_index
              << ")\n";
    std::cout << "A[" << max_index << "] = " << A[max_index] << std::endl;
    std::cout << "B[" << max_index << "] = " << B[max_index] << std::endl;

    if (max_diff > tolerance) {
        std::cout << "\033[1m\033[31m"
                  << "Results don't match.\n"
                  << "\033[0m";
    } else {
        std::cout << "\033[1m\033[32m"
                  << "The results match.\n"
                  << "\033[0m";
    }

    std::cout << std::endl;
}

// Compare result function (compares i64 matrices stored in column-major)
inline hem::i64 compute_max_diff_int(const hem::i64 *A, const hem::i64 *B,
                                     int size) {
    hem::i64 max_diff = 0;
    int max_index = 0;
    for (int i = 0; i < size; ++i) {
        hem::i64 diff = std::abs(A[i] - B[i]);
        if (diff > max_diff) {
            max_diff = diff;
            max_index = i;
        }
    }
    return max_diff;
}

// Compare result function (compares i64 matrices stored in column-major)
inline void compare_matrices_int(const hem::u64 *A, const hem::u64 *B, int size,
                                 hem::i64 tolerance = 0) {
    hem::i64 max_diff = 0;
    int max_index = 0;

    for (int i = 0; i < size; ++i) {
        hem::i64 diff =
            std::abs(static_cast<hem::i64>(A[i]) - static_cast<hem::i64>(B[i]));
        if (diff > max_diff) {
            max_diff = diff;
            max_index = i;
        }
        if (diff > tolerance) {
            // If it exceeds the tolerance, it continues to find the maximum
            // error.
            // return false;
        }
    }
    std::cout << "** Matrix Multiplication Results " << std::endl;
    std::cout << "Maximum error: " << max_diff << " (index: " << max_index
              << ")\n";
    std::cout << "A[" << max_index << "] = " << A[max_index] << std::endl;
    std::cout << "B[" << max_index << "] = " << B[max_index] << std::endl;

    if (max_diff > tolerance) {
        std::cout << "\033[1m\033[31m"
                  << "Results don't match.\n"
                  << "\033[0m";
    } else {
        std::cout << "\033[1m\033[32m"
                  << "The results match.\n"
                  << "\033[0m";
    }

    std::cout << std::endl;
}

// Compare result function (compares i64 matrices stored in column-major)
inline hem::i64 compute_max_diff_int(const hem::u64 *A, const hem::u64 *B,
                                     int size) {
    hem::i64 max_diff = 0;
    int max_index = 0;
    for (int i = 0; i < size; ++i) {
        hem::i64 diff =
            std::abs(static_cast<hem::i64>(A[i]) - static_cast<hem::i64>(B[i]));
        if (diff > max_diff) {
            max_diff = diff;
            max_index = i;
        }
    }
    return max_diff;
}

// Compare result function (compares i64 matrices stored in column-major)
inline void print_compare_matrices_int(std::vector<hem::i64> &total_max_diff,
                                       hem::i64 tolerance = 0) {
    hem::i64 max_diff = 0;
    for (const auto &diff : total_max_diff) {
        if (diff > max_diff) {
            max_diff = diff;
        }
    }

    std::cout << "** Matrix Multiplication Results " << std::endl;
    std::cout << "Maximum error: " << max_diff << "\n";

    if (max_diff > tolerance) {
        std::cout << "\033[1m\033[31m"
                  << "Results don't match.\n"
                  << "\033[0m";
    } else {
        std::cout << "\033[1m\033[32m"
                  << "The results match.\n"
                  << "\033[0m";
    }

    std::cout << std::endl;
}

inline void print_matrix(const hem::i64 *matrix, hem::u64 M, hem::u64 N) {
    for (hem::u64 i = 0; i < M; ++i) {
        for (hem::u64 j = 0; j < N; ++j) {
            std::cout << matrix[i + j * M] << " "; // column-major indexing
        }
        std::cout << std::endl;
    }
}

inline void print_matrix_plain(const hem::i64 *matrix, hem::u64 M, hem::u64 N) {
    std::cout << "(";
    for (hem::u64 i = 0; i < M; ++i) {
        std::cout << "(";
        for (hem::u64 j = 0; j < N; ++j) {
            std::cout << matrix[i + j * M];
            if (j != N - 1)
                std::cout << ","; // column-major indexing
        }
        if (i == M - 1)
            std::cout << ")";
        else
            std::cout << "),";
    }
    std::cout << ")" << std::endl;
}

inline void normalizeMod(hem::i64 a, hem::i64 q, hem::i64 &res) {
    res = a % q;
    if (res < -(q - 1) / 2) {
        res += q;
    } else if (res > (q - 1) / 2) {
        res -= q;
    }
}

// Functions that perform matrix multiplication and modular operations
// (column-major)
// An overflow can occur if 2*k*|A|*|B| > 2^128.
inline void mod_matrix_multiply(const hem::i64 *A, const hem::i64 *B,
                                hem::i64 *C, hem::u64 M, hem::u64 N, hem::u64 K,
                                hem::u64 q) {
    // C is size M x N, A is M x K, and B is K x N.
    for (hem::u64 i = 0; i < M; ++i) {
        for (hem::u64 j = 0; j < N; ++j) {
            u128 sum = 0;
            for (hem::u64 k = 0; k < K; ++k) {
                // A is column-major, B is column-major, C is column-major
                // Multiply (i, k) in A by (k, j) in B
                u128 tmp = static_cast<u128>(A[i + k * M] +
                                             (A[i + k * M] < 0) *
                                                 static_cast<hem::u64>(q)) *
                           static_cast<u128>(B[k + j * K] +
                                             (B[k + j * K] < 0) *
                                                 static_cast<hem::u64>(q));
                sum += tmp;
            }
            normalizeMod(static_cast<hem::i64>(sum % q),
                         static_cast<hem::i64>(q), C[i + j * M]);
        }
    }
}

// Functions that perform matrix multiplication and modular operations
// (column-major)
// An overflow can occur if 2*k*|A|*|B| > 2^128.
inline void mod_matrix_multiply_without_normalize(const hem::i64 *A,
                                                  const hem::i64 *B,
                                                  hem::i64 *C, hem::u64 M,
                                                  hem::u64 N, hem::u64 K,
                                                  hem::u64 q) {
    // C is size M x N, A is M x K, and B is K x N.
    for (hem::u64 i = 0; i < M; ++i) {
        for (hem::u64 j = 0; j < N; ++j) {
            u128 sum = 0;
            for (hem::u64 k = 0; k < K; ++k) {
                // A is column-major, B is column-major, C is column-major
                // Multiply (i, k) in A by (k, j) in B
                u128 tmp = static_cast<u128>(A[i + k * M] +
                                             (A[i + k * M] < 0) *
                                                 static_cast<hem::i64>(q)) *
                           static_cast<u128>(B[k + j * K] +
                                             (B[k + j * K] < 0) *
                                                 static_cast<hem::i64>(q));
                sum += tmp;
            }
            C[i + j * M] = static_cast<hem::i64>(sum % q);
        }
    }
}

// Functions that perform matrix multiplication and modular operations
// (column-major)
// An overflow can occur if 2*k*|A|*|B| > 2^128.
inline void mod_matrix_multiply(const hem::u64 *A, const hem::u64 *B,
                                hem::u64 *C, hem::u64 M, hem::u64 N, hem::u64 K,
                                hem::u64 q) {
    // C is size M x N, A is M x K, and B is K x N.
    for (hem::u64 i = 0; i < M; ++i) {
        for (hem::u64 j = 0; j < N; ++j) {
            u128 sum = 0;
            for (hem::u64 k = 0; k < K; ++k) {
                // A is column-major, B is column-major, C is column-major
                // Multiply (i, k) in A by (k, j) in B
                u128 tmp = static_cast<u128>(A[i + k * M]) *
                           static_cast<u128>(B[k + j * K]);
                sum += tmp;
            }
            C[i + j * M] = static_cast<hem::u64>(sum % q);
        }
    }
}

// Functions that perform matrix multiplication and modular operations
// (column-major)
// An overflow can occur if 2*k*|A|*|B| > 2^128.
inline void mod_matrix_multiply_without_normalize(const hem::u64 *A,
                                                  const hem::u64 *B,
                                                  hem::u64 *C, hem::u64 M,
                                                  hem::u64 N, hem::u64 K,
                                                  hem::u64 q) {
    // C is size M x N, A is M x K, and B is K x N.
    for (hem::u64 i = 0; i < M; ++i) {
        for (hem::u64 j = 0; j < N; ++j) {
            u128 sum = 0;
            for (hem::u64 k = 0; k < K; ++k) {
                // A is column-major, B is column-major, C is column-major
                // Multiply (i, k) in A by (k, j) in B
                u128 tmp = static_cast<u128>(A[i + k * M]) *
                           static_cast<u128>(B[k + j * K]);
                sum += tmp;
            }
            C[i + j * M] = static_cast<hem::u64>(sum % q);
        }
    }
}

inline void mod_matrix_multiply(hem::hemOrder_t order, hem::hemOperation_t op1,
                                hem::hemOperation_t op2, const hem::u64 *A,
                                const hem::u64 *B, hem::u64 *C, hem::u64 M,
                                hem::u64 N, hem::u64 K, hem::u64 q) {
    if (convertTransToOrder(order, op2) == hem::hemColMajor) {
        for (hem::u64 i = 0; i < M; ++i) {
            for (hem::u64 j = 0; j < N; ++j) {
                u128 sum = 0;
                for (hem::u64 l = 0; l < K; ++l) {
                    const auto a_idx =
                        (convertTransToOrder(order, op1) == hem::hemColMajor)
                            ? i + l * M
                            : l + i * K;
                    u128 tmp = static_cast<u128>(A[a_idx]) *
                               static_cast<u128>(B[l + j * K]);
                    sum += tmp;
                }
                const auto c_idx =
                    (order == hem::hemColMajor) ? i + j * M : j + i * N;
                C[c_idx] = static_cast<hem::u64>(sum % q);
            }
        }
    } else {
        for (hem::u64 i = 0; i < M; ++i) {
            std::vector<u128> buffer(N, 0);
            for (hem::u64 l = 0; l < K; ++l) {
                const auto a_idx =
                    (convertTransToOrder(order, op1) == hem::hemColMajor)
                        ? i + l * M
                        : l + i * K;
                u128 op_a = static_cast<u128>(A[a_idx]);
                for (hem::u64 j = 0; j < N; ++j) {
                    const auto op_b = static_cast<u128>(B[j + l * N]);
                    buffer[j] += op_a * op_b;
                }
            }
            for (size_t j = 0; j < N; ++j) {
                const auto c_idx =
                    (order == hem::hemColMajor) ? i + j * M : j + i * N;
                C[c_idx] += static_cast<hem::u64>(buffer[j] % q);
            }
        }
    }
}
