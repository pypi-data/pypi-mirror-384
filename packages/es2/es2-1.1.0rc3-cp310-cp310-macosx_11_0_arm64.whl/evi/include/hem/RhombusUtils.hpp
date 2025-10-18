////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "Rhombus.hpp"
#include <vector>

inline void automorphism(const int *op, int *res, const hem::u64 sig,
                         const hem::u64 degree) {
    // X -> X^{2 * sig + 1}
    hem::u64 base = ((sig << 1) ^ 1) & (2 * degree - 1);
    hem::u64 idx = 0;
    const int *op_ptr = op;
    for (hem::u64 i = 0; i < degree; i++) {
        if (idx & degree)
            res[idx & (degree - 1)] = -*op_ptr;
        else
            res[idx] = *op_ptr;
        op_ptr++;
        idx = (idx + base) & (2 * degree - 1);
    }
}

inline void setEncodingTypeVector(std::vector<HEaaN::Ciphertext> &ctxts,
                                  HEaaN::EncodingType enc_type) {
    for (auto &ct : ctxts) {
        ct.setEncodingType(enc_type);
    }
}

inline void rescaleCiphertexts(std::vector<HEaaN::Ciphertext> &ctxts,
                               HEaaN::HomEvaluator &eval) {
    for (auto &ct : ctxts) {
        ct.setRescaleCounter(1);
        eval.rescale(ct);
    }
}

inline int getLogRhombusScaler(const hem::u64 log_r, const hem::u64 log_c,
                               const hem::u64 log_degree,
                               const hem::RhombusMultType mult_type) {
    return static_cast<int>(
        mult_type == hem::RhombusMultType::RowMajor
            ? std::max(static_cast<int>(log_r + log_c - log_degree), 0)
            : log_c);
}

inline hem::u64 getRhombusStep(const hem::u64 r_pack, const hem::u64 degree,
                               const hem::RhombusMultType mult_type) {
    return mult_type == hem::RhombusMultType::RowMajor
               ? (degree + r_pack - 1) / r_pack
               : 1;
}

// The Optimal Scale Factor
inline void setScaleFactor(hem::u64 *log_scale_factor_W,
                           hem::u64 *log_scale_factor_V, const hem::u64 log_r,
                           const hem::u64 log_c, const hem::u64 modulus,
                           const hem::RhombusMultType mult_type) {
    hem::u64 log_modulus_floor = floor(log2(static_cast<double>(modulus)));
    if (mult_type == hem::RhombusMultType::RowMajor) {
        *log_scale_factor_W = static_cast<hem::u64>(
            round(static_cast<double>(log_modulus_floor) / 2.0 +
                  0.4465 * static_cast<double>(log_r) +
                  0.704 * static_cast<double>(log_c) - 15.7193));
        *log_scale_factor_V = log_modulus_floor - 1 - *log_scale_factor_W;
    } else if (mult_type == hem::RhombusMultType::ColumnMajor) {
        *log_scale_factor_W = static_cast<hem::u64>(
            round(static_cast<double>(log_modulus_floor) / 2.0 -
                  0.1946 * static_cast<double>(log_r) +
                  0.6647 * static_cast<double>(log_c) - 7.6502));
        *log_scale_factor_V = log_modulus_floor - 1 - *log_scale_factor_W;
    }
}

inline void setScaleFactorWithPreprocessedCtxts(
    hem::u64 *log_scale_factor_W, hem::u64 *log_scale_factor_V,
    const hem::u64 log_r, const hem::u64 log_c, const hem::u64 modulus,
    const hem::RhombusMultType mult_type) {
    hem::u64 log_modulus_floor = floor(log2(static_cast<double>(modulus)));
    if (mult_type == hem::RhombusMultType::RowMajor) {
        *log_scale_factor_W = static_cast<hem::u64>(
            round(static_cast<double>(log_modulus_floor) / 2.0 +
                  0.4912 * static_cast<double>(log_r) +
                  0.7303 * static_cast<double>(log_c) - 10.9885));
        *log_scale_factor_V = log_modulus_floor - 1 - *log_scale_factor_W;
    } else if (mult_type ==
               hem::RhombusMultType::ColumnMajor) { // not calculated
        *log_scale_factor_W = static_cast<hem::u64>(
            round(static_cast<double>(log_modulus_floor) / 2.0 -
                  0.1946 * static_cast<double>(log_r) +
                  0.6647 * static_cast<double>(log_c) - 7.6502));
        *log_scale_factor_V = log_modulus_floor - 1 - *log_scale_factor_W;
    }
}
