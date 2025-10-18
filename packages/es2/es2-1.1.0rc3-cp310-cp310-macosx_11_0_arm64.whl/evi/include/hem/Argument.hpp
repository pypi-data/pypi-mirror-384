////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"

#define DOUBLE_PREC_BITS 53
#define INT8_SIZE 7

inline hem::u64 computeScaleBit(hem::u64 scale) {
    if (scale == 0) {
        return 0;
    }
    hem::u64 scale_bit = 0;
    while (scale > 0) {
        scale >>= 1;
        ++scale_bit;
    }
    return scale_bit;
}

inline hem::u64 computeWordSizeForPCMM(hem::u64 scale_bit_a, int k) {
    return DOUBLE_PREC_BITS - scale_bit_a - computeScaleBit(k);
}
