////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/ModulusEngine.hpp"
#include "hem/PPMMUtils.hpp"

namespace hem {

template <hemNative_t M = NONE, typename T>
void ppmmModNativeCPU(hemOrder_t order, hemOperation_t transa,
                      hemOperation_t transb, const T *A, const T *B, T *C,
                      int m, int n, int k,
                      const ModulusEngineUnit &engine_unit);

template <hemNative_t M = NONE, typename T>
void ppmmModNativeGPU(hemOrder_t order, hemOperation_t transa,
                      hemOperation_t transb, const T *A, const T *B, T *C,
                      int m, int n, int k,
                      const ModulusEngineUnit &engine_unit);

// PPMM with BLAS

void ppmmFP64CPU(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
                 const double *A, const double *B, double *C, int m, int n,
                 int k, double alpha, double beta);

void ppmmModFP64CPU(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const i64 *A, const i64 *B, i64 *C,
                    int m, int n, int k, const ModulusEngineUnit &engine_unit,
                    u64 word_size);

void ppmmModFP64OptBCPU(hemOrder_t order, hemOperation_t transa,
                        hemOperation_t transb, const i64 *A, const i64 *B,
                        i64 *C, int m, int n, int k,
                        const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedFP64CPU(hemOrder_t order, hemOperation_t transa,
                                hemOperation_t transb, const i64 *A,
                                const double *b_real_a, const double *b_real_b,
                                i64 *C_a, i64 *C_b, int m, int n, int k,
                                const ModulusEngineUnit &engine_unit,
                                u64 word_size);

void ppmmModPreprocessedFP64OptBCPU(hemOrder_t order, hemOperation_t transa,
                                    hemOperation_t transb, const i64 *A,
                                    const double *b_real_a,
                                    const double *b_real_b, i64 *C_a, i64 *C_b,
                                    int m, int n, int k,
                                    const ModulusEngineUnit &engine_unit,
                                    u64 word_size);

void ppmmModPreprocessedFP64HalfOptBCPU(hemOrder_t order, hemOperation_t transa,
                                        hemOperation_t transb, const i64 *A,
                                        const double *b_real_b, i64 *C_b, int m,
                                        int n, int k,
                                        const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedHalfFP64CPU(hemOrder_t order, hemOperation_t transa,
                                    hemOperation_t transb, const i64 *A,
                                    const double *b_real_a, i64 *C_a, int m,
                                    int n, int k,
                                    const ModulusEngineUnit &engine_unit,
                                    u64 word_size);

void rescaleAPartCPU(i64 *C_0, i64 *C_1, u64 size, const ModulusEngine &engine);

void ppmmModPreprocessedFP64ApproxCPU(hemOrder_t order, hemOperation_t transa,
                                      hemOperation_t transb, const i64 *A,
                                      const double *b_real_b, i64 *C_b, int m,
                                      int n, int k,
                                      const ModulusEngine &engine);

void preprocessFP64CPU(const i64 *B_a, const i64 *B_b, double *b_real_a,
                       double *b_real_b, int m, int n,
                       const ModulusEngineUnit &engine_unit, u64 word_size,
                       bool opt_b = false);

void preprocessFP64ApproxCPU(const i64 *B_0, const i64 *B_1, double *b_real_0,
                             int m, int n, const ModulusEngine &engine);

void transposeMatricesCPU(const i64 *A, i64 *TA, int m, int n);

// Unsigned integer version

void ppmmModFP64CPU(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const u64 *A, const u64 *B, u64 *C,
                    int m, int n, int k, const ModulusEngineUnit &engine_unit,
                    u64 word_size);

void ppmmModFP64OptBCPU(hemOrder_t order, hemOperation_t transa,
                        hemOperation_t transb, const u64 *A, const u64 *B,
                        u64 *C, int m, int n, int k,
                        const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedFP64CPU(hemOrder_t order, hemOperation_t transa,
                                hemOperation_t transb, const u64 *A,
                                const double *b_real_a, const double *b_real_b,
                                u64 *C_a, u64 *C_b, int m, int n, int k,
                                const ModulusEngineUnit &engine_unit,
                                u64 word_size);

void ppmmModPreprocessedFP64OptBCPU(hemOrder_t order, hemOperation_t transa,
                                    hemOperation_t transb, const u64 *A,
                                    const double *b_real_a,
                                    const double *b_real_b, u64 *C_a, u64 *C_b,
                                    int m, int n, int k,
                                    const ModulusEngineUnit &engine_unit,
                                    u64 word_size);

void ppmmModPreprocessedFP64HalfOptBCPU(hemOrder_t order, hemOperation_t transa,
                                        hemOperation_t transb, const u64 *A,
                                        const double *b_real_b, u64 *C_b, int m,
                                        int n, int k,
                                        const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedFP64ApproxCPU(hemOrder_t order, hemOperation_t transa,
                                      hemOperation_t transb, const u64 *A,
                                      const double *b_real_b, u64 *C_b, int m,
                                      int n, int k,
                                      const ModulusEngine &engine);

void preprocessFP64CPU(const u64 *B_a, const u64 *B_b, double *b_real_a,
                       double *b_real_b, int m, int n,
                       const ModulusEngineUnit &engine_unit, u64 word_size,
                       bool opt_b = false);

void preprocessFP64ApproxCPU(const u64 *B_0, const u64 *B_1, double *b_real_0,
                             int m, int n, const ModulusEngine &engine);

void transposeMatricesCPU(const u64 *A, u64 *TA, int m, int n);

// GPU functions
void ppmmFP64GPU(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
                 const double *A, const double *B, double *C, int m, int n,
                 int k, double alpha, double beta);

void ppmmModFP64GPU(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const i64 *A, const i64 *B, i64 *C,
                    int m, int n, int k, const ModulusEngineUnit &engine_unit,
                    u64 word_size);

void ppmmModFP64OptBGPU(hemOrder_t order, hemOperation_t transa,
                        hemOperation_t transb, const i64 *A, const i64 *B,
                        i64 *C, int m, int n, int k,
                        const ModulusEngineUnit &engine_unit);

void preprocessFP64GPU(const i64 *B_a, const i64 *B_b, double *b_real_a,
                       double *b_real_b, int m, int n,
                       const ModulusEngineUnit &engine_unit, u64 word_size,
                       bool opt_b = false);

void preprocessFP64ApproxGPU(const i64 *B_0, const i64 *B_1, double *b_real_0,
                             int m, int n, const ModulusEngine &engine);

void ppmmModPreprocessedFP64GPU(hemOrder_t order, hemOperation_t transa,
                                hemOperation_t transb, const i64 *A,
                                const double *b_real_a, const double *b_real_b,
                                i64 *C_a, i64 *C_b, int m, int n, int k,
                                const ModulusEngineUnit &engine_unit,
                                u64 word_size);

void ppmmModPreprocessedFP64OptBGPU(hemOrder_t order, hemOperation_t transa,
                                    hemOperation_t transb, const i64 *A,
                                    const double *b_real_a,
                                    const double *b_real_b, i64 *C_a, i64 *C_b,
                                    int m, int n, int k,
                                    const ModulusEngineUnit &engine_unit,
                                    u64 word_size);

void ppmmModPreprocessedFP64HalfOptBGPU(hemOrder_t order, hemOperation_t transa,
                                        hemOperation_t transb, const i64 *A,
                                        const double *b_real_b, i64 *C_b, int m,
                                        int n, int k,
                                        const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedHalfFP64GPU(hemOrder_t order, hemOperation_t transa,
                                    hemOperation_t transb, const i64 *A,
                                    const double *b_real_a, i64 *C_a, int m,
                                    int n, int k,
                                    const ModulusEngineUnit &engine_unit,
                                    u64 word_size);

void rescaleAPartGPU(i64 *C_0, i64 *C_1, u64 size, const ModulusEngine &engine);

void ppmmModPreprocessedFP64ApproxGPU(hemOrder_t order, hemOperation_t transa,
                                      hemOperation_t transb, const i64 *A,
                                      const double *b_real_b, i64 *C_b, int m,
                                      int n, int k,
                                      const ModulusEngine &engine);

void ppmmInt8GPU(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
                 const i8 *a, const i8 *b, i32 *c, int m, int n, int k,
                 int alpha, int beta);

void ppmmModInt8GPU(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const i64 *A, const i64 *B, i64 *C,
                    int m, int n, int k, const ModulusEngineUnit &engine_unit,
                    u64 scale_bit_a);

void preprocessInt8GPU(const i64 *B_a, const i64 *B_b, i8 *b_int8_a,
                       i8 *b_int8_b, int m, int n,
                       const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedInt8GPU(hemOrder_t order, hemOperation_t transa,
                                hemOperation_t transb, const i64 *A,
                                const i8 *b_int8_a, const i8 *b_int8_b,
                                i64 *C_a, i64 *C_b, int m, int n, int k,
                                const ModulusEngineUnit &engine_unit,
                                u64 scale_bit_a);

void transposeMatricesGPU(const i64 *A, i64 *TA, int m, int n);

// Unsigned integer version

void ppmmModFP64GPU(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const u64 *A, const u64 *B, u64 *C,
                    int m, int n, int k, const ModulusEngineUnit &engine_unit,
                    u64 word_size);

void ppmmModFP64OptBGPU(hemOrder_t order, hemOperation_t transa,
                        hemOperation_t transb, const u64 *A, const u64 *B,
                        u64 *C, int m, int n, int k,
                        const ModulusEngineUnit &engine_unit);

void preprocessFP64GPU(const u64 *B_a, const u64 *B_b, double *b_real_a,
                       double *b_real_b, int m, int n,
                       const ModulusEngineUnit &engine_unit, u64 word_size,
                       bool opt_b = false);

void preprocessFP64ApproxGPU(const u64 *B_0, const u64 *B_1, double *b_real_0,
                             int m, int n, const ModulusEngine &engine);

void ppmmModPreprocessedFP64GPU(hemOrder_t order, hemOperation_t transa,
                                hemOperation_t transb, const u64 *A,
                                const double *b_real_a, const double *b_real_b,
                                u64 *C_a, u64 *C_b, int m, int n, int k,
                                const ModulusEngineUnit &engine_unit,
                                u64 word_size);

void ppmmModPreprocessedFP64OptBGPU(hemOrder_t order, hemOperation_t transa,
                                    hemOperation_t transb, const u64 *A,
                                    const double *b_real_a,
                                    const double *b_real_b, u64 *C_a, u64 *C_b,
                                    int m, int n, int k,
                                    const ModulusEngineUnit &engine_unit,
                                    u64 word_size);

void ppmmModPreprocessedFP64HalfOptBGPU(hemOrder_t order, hemOperation_t transa,
                                        hemOperation_t transb, const u64 *A,
                                        const double *b_real_b, u64 *C_b, int m,
                                        int n, int k,
                                        const ModulusEngineUnit &engine_unit);

void ppmmModInt8GPU(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const u64 *A, const u64 *B, u64 *C,
                    int m, int n, int k, const ModulusEngineUnit &engine_unit,
                    u64 scale_bit_a);

void preprocessInt8GPU(const u64 *B_a, const u64 *B_b, i8 *b_int8_a,
                       i8 *b_int8_b, int m, int n,
                       const ModulusEngineUnit &engine_unit);

void ppmmModPreprocessedInt8GPU(hemOrder_t order, hemOperation_t transa,
                                hemOperation_t transb, const u64 *A,
                                const i8 *b_int8_a, const i8 *b_int8_b,
                                u64 *C_a, u64 *C_b, int m, int n, int k,
                                const ModulusEngineUnit &engine_unit,
                                u64 scale_bit_a);

void transposeMatricesGPU(const u64 *A, u64 *TA, int m, int n);

} // namespace hem
