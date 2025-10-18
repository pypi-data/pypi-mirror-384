////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once
// TODO: Remove this file and make another file for HEM.
// This file is a copy of the original file from HEAAN library.
// The original file is located at HEAAN/impl/Arith.hpp.

#include "hem/DataType.hpp"

#include <algorithm>
#include <cmath>

#ifdef HEAAN_USE_ABSL_INT128
#include <absl/numeric/int128.h>
#endif

namespace HEaaN {

#ifdef HEAAN_USE_ABSL_INT128
using u128 = absl::uint128;
using i128 = absl::int128;
#else
using u128 = unsigned __int128;
using i128 = __int128;
#endif

#define U64C(x) UINT64_C(x)
#define U128C(lo, hi) ((static_cast<u128>(U64C(hi)) << 64) + (lo))

inline hem::u64 u128Lo(u128 x) { return static_cast<hem::u64>(x); }

inline hem::u64 u128Hi(u128 x) { return static_cast<hem::u64>(x >> 64); }

inline u128 u128FromU64(hem::u64 lo, hem::u64 hi = hem::U64ZERO) {
    return (static_cast<u128>(hi) << 64) | (static_cast<u128>(lo));
}

} // namespace HEaaN

namespace HEaaN::arith {

inline hem::u64 countLeftZeroes(hem::u64 op) {
#ifndef __has_builtin
#define __has_builtin(arg) 0
#endif
#if __has_builtin(__builtin_clzll)
    return static_cast<hem::u64>(__builtin_clzll(op));
#elif _MSC_VER
    return static_cast<hem::u64>(__lzcnt64(op));
#else
    // Algorithm: see "Hacker's delight" 2nd ed., section 5.13, algorithm 5-12.
    hem::u64 n = 64;
    hem::u64 tmp;
    tmp = op >> 32;
    if (tmp != 0) {
        n = n - 32;
        op = tmp;
    }
    tmp = op >> 16;
    if (tmp != 0) {
        n = n - 16;
        op = tmp;
    }
    tmp = op >> 8;
    if (tmp != 0) {
        n = n - 8;
        op = tmp;
    }
    tmp = op >> 4;
    if (tmp != 0) {
        n = n - 4;
        op = tmp;
    }
    tmp = op >> 2;
    if (tmp != 0) {
        n = n - 2;
        op = tmp;
    }
    tmp = op >> 1;
    if (tmp != 0)
        return n - 2;
    return n - op;
#endif
}

// Return bit width of the given parameter op.
// - If op equals to 0, then it returns 0. If op is positive, then it returns
// floor(log_2 op) + 1.
// - op is constraint to have unsigned long long type only.
// - TODO(TK): Replace this with std::bit_width (C++20).
inline hem::u64 bitWidth(const hem::u64 op) {
    return op ? U64C(64) - countLeftZeroes(op) : hem::U64ZERO;
}

// Integral log2 with log2floor(0) := 0
inline hem::u64 log2floor(const hem::u64 op) {
    return op ? bitWidth(op) - 1 : hem::U64ZERO;
}

inline uint32_t bitReverse32(uint32_t x) {
    x = (((x & 0xaaaaaaaa) >> 1) | ((x & 0x55555555) << 1));
    x = (((x & 0xcccccccc) >> 2) | ((x & 0x33333333) << 2));
    x = (((x & 0xf0f0f0f0) >> 4) | ((x & 0x0f0f0f0f) << 4));
    x = (((x & 0xff00ff00) >> 8) | ((x & 0x00ff00ff) << 8));
    return ((x >> 16) | (x << 16));
}

inline uint32_t bitReverse(uint32_t x, hem::u64 max_digits) {
    return bitReverse32(x) >> (32 - max_digits);
}

inline bool isPowerOfTwo(hem::u64 op) { return op && (!(op & (op - 1))); }

template <typename T> void bitReverseArray(T *data, hem::u64 n) {
    if (!(isPowerOfTwo(n)))
        return;

    for (hem::u64 i = hem::U64ONE, j = hem::U64ZERO; i < n; ++i) {
        hem::u64 bit = n >> 1;
        for (; j >= bit; bit >>= 1)
            j -= bit;

        j += bit;
        if (i < j)
            std::swap(data[i], data[j]);
    }
}

// Divide a 128 bit integer by a 64 bit integer and return the quotient.
// x_hi : The highest 64 bit of a 128 bit integer.
// x_lo : The lowest 64 bit of a 128 bit integer.
// returns Quotient of x divided by y.
inline hem::u64 divide128By64Lo(hem::u64 x_hi, hem::u64 x_lo, hem::u64 y) {
    return static_cast<hem::u64>(u128FromU64(x_lo, x_hi) / y);
}

inline u128 mul64To128(const hem::u64 op1, const hem::u64 op2) {
    return static_cast<u128>(op1) * op2;
}

inline void mul64To128(hem::u64 a, hem::u64 b, hem::u64 &hi, hem::u64 &lo) {
    u128 mul = mul64To128(a, b);
    hi = u128Hi(mul);
    lo = u128Lo(mul);
}

inline hem::u64 mul64To128Hi(const hem::u64 op1, const hem::u64 op2) {
    u128 mul = mul64To128(op1, op2);
    return u128Hi(mul);
}

inline hem::u64 mulModSimple(hem::u64 a, hem::u64 b, hem::u64 mod) {
    return static_cast<hem::u64>(arith::mul64To128(a, b) % mod);
}

inline hem::u64 powModSimple(hem::u64 base, hem::u64 expo, hem::u64 mod) {
    hem::u64 res = 1;
    while (expo > 0) {
        if (expo & 1) // if odd
            res = mulModSimple(res, base, mod);
        base = mulModSimple(base, base, mod);
        expo >>= 1;
    }

    return res;
}

inline hem::u64 invModSimple(hem::u64 a, hem::u64 modulus) {
    return powModSimple(a, modulus - 2, modulus);
}

inline hem::u64 mulModLazy(const hem::u64 x, const hem::u64 y,
                           const hem::u64 y_barrett, const hem::u64 mod) {
    hem::u64 q = arith::mul64To128Hi(x, y_barrett);
    return y * x - q * mod;
}

inline hem::u64 subIfGE(hem::u64 a, hem::u64 b) { return (a >= b ? a - b : a); }

inline hem::u64 reduceBarrett(hem::u64 op, const hem::u64 modulus,
                              const hem::u64 barr_for_64) {
    hem::u64 approx_quotient = arith::mul64To128Hi(op, barr_for_64);
    hem::u64 res = op - approx_quotient * modulus;
    // res in [0, 2*modulus)
    res = arith::subIfGE(res, modulus);
    return res;
}

void addVector(hem::u64 *res, const hem::u64 *op1, const hem::u64 *op2,
               const hem::u64 modulus, const hem::u64 array_size);

void subVector(hem::u64 *res, const hem::u64 *op1, const hem::u64 *op2,
               const hem::u64 modulus, const hem::u64 array_size);

void mulVector(hem::u64 *res, const hem::u64 *op1, const hem::u64 *op2,
               const hem::u64 modulus, const hem::u64 array_size);

void mulAddVector(hem::u64 *res, const hem::u64 *op1, const hem::u64 *op2,
                  const hem::u64 modulus, const hem::u64 array_size);

} // namespace HEaaN::arith
