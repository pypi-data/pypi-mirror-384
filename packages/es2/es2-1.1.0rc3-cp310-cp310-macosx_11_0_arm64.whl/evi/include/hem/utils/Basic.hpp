////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once
// This file is a copy of the original file from HEAAN library.
// The original file is located at HEAAN/impl/Basic.cuh

#include "hem/DataType.hpp"
#include "hem/utils/Macros.hpp"

#if defined(HEM_USE_CUDA) || defined(HEM_USE_HIP)

#if defined(HEM_USE_CUDA)

struct u128_t {
    hem::u64 hi;
    hem::u64 lo;
    explicit CUDA_CALLABLE u128_t() : hi{0}, lo{0} {}
    explicit CUDA_CALLABLE u128_t(const hem::u64 x) : hi{0}, lo{x} {}
    CUDA_CALLABLE_INLINE u128_t &operator+=(const u128_t &op) {
        asm("add.cc.u64 %1, %3, %1;\n\t"
            "addc.u64 %0, %2, %0;\n\t"
            : "+l"(hi), "+l"(lo)
            : "l"(op.hi), "l"(op.lo));
        return *this;
    }
};

#elif defined(HEM_USE_HIP)

struct u128_t {
    hem::u64 hi;
    hem::u64 lo;
    explicit CUDA_CALLABLE u128_t() : hi{0}, lo{0} {}
    explicit CUDA_CALLABLE u128_t(const hem::u64 x) : hi{0}, lo{x} {}
    CUDA_CALLABLE_INLINE u128_t &operator+=(const u128_t &op) {
        hem::u64 lo_ = this->lo;
        this->lo += op.lo;
        this->hi += op.hi + (this->lo < lo_);
        return *this;
    }
};

#endif

CUDA_CALLABLE_INLINE hem::u64 __umul64hi(hem::u64 x, hem::u64 y) {
    __uint128_t result = (__uint128_t)x * (__uint128_t)y;
    return (hem::u64)(result >> 64);
}

// This algorithm works well for any integer in [0, 2^128).
// It is based on Shoup algorithm.
template <int OutputModFactor = 1>
CUDA_CALLABLE_INLINE hem::u64
reduceBarrett(const u128_t &op, const hem::u64 modulus,
              const hem::u64 two_modulus, const hem::u64 barr_for_64,
              const hem::u64 two_to_64, const hem::u64 two_to_64_shoup) {
    hem::u64 hi = op.hi;
    hem::u64 lo = op.lo;

    hem::u64 q = __umul64hi(hi, two_to_64_shoup) + __umul64hi(lo, barr_for_64);
    hem::u64 res = hi * two_to_64 + lo;
    res -= q * modulus;

    if constexpr (OutputModFactor <= 2) {
        res = (res >= two_modulus) ? res - two_modulus : res;
        if constexpr (OutputModFactor == 1) {
            res = (res >= modulus) ? res - modulus : res;
        }
    }
    return res;
}

CUDA_CALLABLE_INLINE hem::u64 computeScaleBitGPU(hem::u64 scale) {
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

#endif
