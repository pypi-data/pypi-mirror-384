////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/ModulusEngine.hpp"
#include "hem/ModulusMatrix.hpp"
#include "hem/PPMM.hpp"
#include <optional>

namespace hem {

template <typename T>
void pcmmFP64(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
              const PTMatrix<T> &a, const CTMatrix<T> &b, CTMatrix<T> &c,
              const ModulusEngine &engine, u64 word_size, bool opt_b = false);

// preprocessed b
template <typename T>
void pcmmFP64(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
              const PTMatrix<T> &a, const CTMatrix<double> &b, CTMatrix<T> &c,
              const ModulusEngine &engine, u64 word_size, bool opt_b = false);

void pcmmFP64Approx(hemOrder_t order, hemOperation_t transa,
                    hemOperation_t transb, const PTMatrix<i64> &a,
                    const CTMatrix<double> &b, const CTMatrix<double> &b_opt,
                    CTMatrix<i64> &c, const ModulusEngine &engine,
                    u64 word_size);

/* deprecated */
template <typename T>
void pcmmInt8(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
              const PTMatrix<T> &a, const CTMatrix<T> &b, CTMatrix<T> &c,
              const ModulusEngine &engine);

// preprocessed b
template <typename T>
void pcmmInt8(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
              const PTMatrix<T> &a, const CTMatrix<i8> &b, CTMatrix<T> &c,
              const ModulusEngine &engine);

template <hemNative_t M = NONE, typename T>
void pcmmNative(hemOrder_t order, hemOperation_t transa, hemOperation_t transb,
                const PTMatrix<T> &a, const CTMatrix<T> &b, CTMatrix<T> &c,
                const ModulusEngine &engine, bool opt_b = false,
                const std::optional<CTMatrix<double>> &b_prep = std::nullopt);

} // namespace hem
