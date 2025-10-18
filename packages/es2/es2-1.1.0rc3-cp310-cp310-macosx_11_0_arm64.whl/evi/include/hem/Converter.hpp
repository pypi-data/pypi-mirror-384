////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Context.hpp"
#include "HEaaN/ModPackKeyBundle.hpp"
#include "hem/ModulusMatrix.hpp"

namespace hem {

//
// CTMatrix version
//
template <typename T>
void convertRowMajorRLWEsToColumnMajorMatrices(
    const std::vector<HEaaN::Ciphertext> &ctxt, CTMatrix<T> &mat);

template <typename T>
void convertColumnMajorMatricesToRowMajorRLWEs(
    const CTMatrix<T> &mat, std::vector<HEaaN::Ciphertext> &ctxt);

template <typename T>
void convertRowMajorRLWEsToRowMajorMatrices(
    const std::vector<HEaaN::Ciphertext> &ctxt, CTMatrix<T> &mat);

template <typename T>
void convertRowMajorMatricesToRowMajorRLWEs(
    const CTMatrix<T> &mat, std::vector<HEaaN::Ciphertext> &ctxt);

//
// Signed integer version
//

void convertRowMajorMatricesToRowMajorRLWEsCPU(
    const i64 *A, const i64 *B, u64 k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

void convertRowMajorRLWEsToColumnMajorMatricesCPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, i64 *A, i64 *B, u64 k,
    u64 target_level);

void convertColumnMajorMatricesToRowMajorRLWEsCPU(
    const i64 *A, const i64 *B, u64 k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

void convertRowMajorRLWEsToRowMajorMatricesCPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, i64 *A, i64 *B, u64 k,
    u64 target_level);

//
// Unsigned integer version
//

void convertRowMajorMatricesToRowMajorRLWEsCPU(
    const u64 *A, const u64 *B, size_t k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

void convertRowMajorRLWEsToColumnMajorMatricesCPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, u64 *A, u64 *B, size_t k,
    u64 target_level);

void convertColumnMajorMatricesToRowMajorRLWEsCPU(
    const u64 *A, const u64 *B, size_t k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

void convertRowMajorRLWEsToRowMajorMatricesCPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, u64 *A, u64 *B, size_t k,
    u64 target_level);

// GPU functions
//
// Signed integer version
//

void convertRowMajorRLWEsToColumnMajorMatricesGPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, i64 *A, i64 *B, u64 k,
    u64 target_level);

void convertColumnMajorMatricesToRowMajorRLWEsGPU(
    const i64 *A, const i64 *B, u64 k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

void convertRowMajorRLWEsToRowMajorMatricesGPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, i64 *A, i64 *B, u64 k,
    u64 target_level);

void convertRowMajorMatricesToRowMajorRLWEsGPU(
    const i64 *A, const i64 *B, u64 k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

//
// Unsigned integer version
//

void convertRowMajorRLWEsToColumnMajorMatricesGPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, u64 *A, u64 *B, size_t k,
    u64 target_level);

void convertColumnMajorMatricesToRowMajorRLWEsGPU(
    const u64 *A, const u64 *B, size_t k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

void convertRowMajorRLWEsToRowMajorMatricesGPU(
    const std::vector<HEaaN::Ciphertext> &ctxt, u64 *A, u64 *B, size_t k,
    u64 target_level);

void convertRowMajorMatricesToRowMajorRLWEsGPU(
    const u64 *A, const u64 *B, size_t k, std::vector<HEaaN::Ciphertext> &ctxt,
    u64 target_level);

//
// MLWE Functions
//
void convertRLWEsToMLWEs(const std::vector<HEaaN::Ciphertext> &ctxt,
                         std::vector<HEaaN::MLWECiphertext> &ctxt_res,
                         const HEaaN::Context &context_hi,
                         const HEaaN::Context &context_lo, const u64 k);

void convertRLWEsToMLWEsCPU(const std::vector<HEaaN::Ciphertext> &ctxt,
                            std::vector<HEaaN::MLWECiphertext> &ctxt_res,
                            const HEaaN::Context &context_hi,
                            const HEaaN::Context &context_lo, const u64 k);

void convertRLWEsToMLWEsGPU(const std::vector<HEaaN::Ciphertext> &ctxt,
                            std::vector<HEaaN::MLWECiphertext> &ctxt_res,
                            const HEaaN::Context &context_hi,
                            const HEaaN::Context &context_lo, const u64 k);

void convertRowMajorMLWEsToColumnMajorMatrices(
    const std::vector<HEaaN::MLWECiphertext> &ctxt, CTMatrix<u64> &mat);

void convertRowMajorMLWEsToColumnMajorMatricesCPU(
    const std::vector<HEaaN::MLWECiphertext> &ctxt, CTMatrix<u64> &mat,
    const u64 target_level);

void convertRowMajorMLWEsToColumnMajorMatricesGPU(
    const std::vector<HEaaN::MLWECiphertext> &ctxt, CTMatrix<u64> &mat,
    const u64 target_level);

void convertRowMajorMLWEsToRowMajorMatrices(
    const std::vector<HEaaN::MLWECiphertext> &ctxt, CTMatrix<u64> &mat);

void convertRowMajorMLWEsToRowMajorMatricesCPU(
    const std::vector<HEaaN::MLWECiphertext> &ctxt, CTMatrix<u64> &mat,
    const u64 target_level);

void convertRowMajorMLWEsToRowMajorMatricesGPU(
    const std::vector<HEaaN::MLWECiphertext> &ctxt, CTMatrix<u64> &mat,
    const u64 target_level);

void convertColumnMajorMatricesToRowMajorMLWEs(
    const CTMatrix<u64> &mat, std::vector<HEaaN::MLWECiphertext> &ctxt);

void convertColumnMajorMatricesToRowMajorMLWEsCPU(
    const CTMatrix<u64> &mat, std::vector<HEaaN::MLWECiphertext> &ctxt,
    const u64 target_level);

void convertColumnMajorMatricesToRowMajorMLWEsGPU(
    const CTMatrix<u64> &mat, std::vector<HEaaN::MLWECiphertext> &ctxt,
    const u64 target_level);

void convertMLWEsToRLWEs(const std::vector<HEaaN::MLWECiphertext> &ctxt_mlwe,
                         std::vector<HEaaN::Ciphertext> &ctxt_res,
                         const HEaaN::Context &context_hi,
                         const HEaaN::Context &context_lo,
                         const HEaaN::ModPackKeyBundle &modpack_keys);

void convertMLWEsToRLWEsCPU(const std::vector<HEaaN::MLWECiphertext> &ctxt_mlwe,
                            std::vector<HEaaN::Ciphertext> &ctxt_res,
                            const HEaaN::Context &context_hi,
                            const HEaaN::Context &context_lo,
                            const HEaaN::ModPackKeyBundle &modpack_keys);

void convertMLWEsToRLWEsGPU(const std::vector<HEaaN::MLWECiphertext> &ctxt_mlwe,
                            std::vector<HEaaN::Ciphertext> &ctxt_res,
                            const HEaaN::Context &context_hi,
                            const HEaaN::Context &context_lo,
                            const HEaaN::ModPackKeyBundle &modpack_keys);

} // namespace hem
