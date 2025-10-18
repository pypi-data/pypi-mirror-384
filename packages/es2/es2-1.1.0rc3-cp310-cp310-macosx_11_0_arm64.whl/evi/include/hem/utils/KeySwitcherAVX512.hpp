////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"

namespace HEaaN::KeySwitcher {

void constMultByDegreeAVX512DQ(const hem::u64 *op, const hem::u64 *coeff,
                               hem::u64 *res, hem::u64 array_size,
                               const hem::u64 log_degree,
                               const hem::u64 *moduli);
void normalizeModVectorAVX512DQ(hem::u64 *res, const hem::u64 *op,
                                const hem::u64 op1_modulus,
                                const hem::u64 modulus,
                                const hem::u64 array_size, const hem::i64 diff);
template <bool AddToResult>
void normalizeModAndConstMultAVX512DQ(const hem::u64 *op1, const hem::u64 op2,
                                      const hem::u64 op1_modulus,
                                      const hem::u64 modulus, hem::u64 *res,
                                      const hem::u64 array_size,
                                      const hem::u64 diff);
void constMultAVX512DQ(const hem::u64 *op1, const hem::u64 op2, hem::u64 *res,
                       hem::u64 array_size, const hem::u64 modulus);

void subAndConstMult512DQ(const hem::u64 *op1, const hem::u64 *op2,
                          const hem::u64 op3, hem::u64 *res,
                          hem::u64 array_size, const hem::u64 modulus);
} // namespace HEaaN::KeySwitcher
