////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/ModulusEngine.hpp"
#include "hem/ModulusMatrix.hpp"

namespace hem {

template <typename T>
void preprocessFP64(const CTMatrix<T> &B, CTMatrix<double> &b,
                    const ModulusEngine &engine, u64 word_size,
                    bool opt_b = false);

template <typename T>
void preprocessFP64Approx(const CTMatrix<T> &B, CTMatrix<double> &b,
                          const ModulusEngine &engine);

template <typename T>
void preprocessInt8(const CTMatrix<T> &B, CTMatrix<i8> &b,
                    const ModulusEngine &engine);

} // namespace hem
