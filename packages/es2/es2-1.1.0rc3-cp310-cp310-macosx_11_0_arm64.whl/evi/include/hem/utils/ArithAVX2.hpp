////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/utils/Arith.hpp"
#include <immintrin.h>

#if defined(_MSC_VER)
#include <intrin.h>
#endif // _MSC_VER

namespace HEaaN::arith {

// (a >= b) ? (a - b) : a
inline __m256i subIfGE(__m256i a, __m256i b) {
    // original code
    // static const __m256i sign =
    //     _mm256_set1_epi64x(U64ONE << 63); // 1000...00 in binary
    // __m256i mask = _mm256_cmpgt_epi64(_mm256_xor_si256(b, sign),
    //                                   _mm256_xor_si256(a, sign));

    // This code needs to assume that a, b < 2^63.
    // You must not use the modulus greater than 2^61.
    __m256i mask = _mm256_cmpgt_epi64(b, a);
    __m256i res = _mm256_sub_epi64(a, b);
    res = _mm256_add_epi64(res, _mm256_and_si256(b, mask));
    return res;
}

inline void mul64To128(__m256i a, __m256i b, __m256i &hi, __m256i &lo) {
    static const __m256i LOWER32BITS = _mm256_set1_epi64x(U64C(0xFFFFFFFF));
    auto ah = _mm256_srli_epi64(a, 32);
    auto bh = _mm256_srli_epi64(b, 32);
    auto ll = _mm256_mul_epu32(a, b);
    auto lh = _mm256_mul_epu32(a, bh);
    auto hl = _mm256_mul_epu32(ah, b);
    auto hh = _mm256_mul_epu32(ah, bh);

    auto s1 = _mm256_add_epi64(lh, _mm256_srli_epi64(ll, 32));
    auto s2 = _mm256_add_epi64(hl, _mm256_and_si256(s1, LOWER32BITS));
    auto s3 = _mm256_add_epi64(hh, _mm256_srli_epi64(s1, 32));

    hi = _mm256_add_epi64(s3, _mm256_srli_epi64(s2, 32));
    lo = _mm256_or_si256(_mm256_slli_epi64(s2, 32),
                         _mm256_and_si256(ll, LOWER32BITS));
}

inline __m256i mul64To128Lo(__m256i a, __m256i b) {
    __m256i ll = _mm256_mul_epu32(a, b);
    __m256i mid = _mm256_mul_epu32(a, _mm256_srli_epi64(b, 32));
    mid = _mm256_add_epi64(mid, _mm256_mul_epu32(_mm256_srli_epi64(a, 32), b));
    return _mm256_add_epi64(ll, _mm256_slli_epi64(mid, 32));
}

inline __m256i mul64To128Hi(__m256i a, __m256i b) {
    static const __m256i LOWER32BITS = _mm256_set1_epi64x(U64C(0xFFFFFFFF));
    auto ah = _mm256_srli_epi64(a, 32);
    auto bh = _mm256_srli_epi64(b, 32);
    auto ll = _mm256_mul_epu32(a, b);
    auto lh = _mm256_mul_epu32(a, bh);
    auto hl = _mm256_mul_epu32(ah, b);
    auto hh = _mm256_mul_epu32(ah, bh);

    auto s1 = _mm256_add_epi64(lh, _mm256_srli_epi64(ll, 32));
    auto s2 = _mm256_add_epi64(hl, _mm256_and_si256(s1, LOWER32BITS));
    auto s3 = _mm256_add_epi64(hh, _mm256_srli_epi64(s1, 32));

    return _mm256_add_epi64(s3, _mm256_srli_epi64(s2, 32));
}

inline __m256i mul64To128HiApprox(__m256i a, __m256i b) {
    static const __m256i LOWER32BITS = _mm256_set1_epi64x(U64C(0xFFFFFFFF));
    auto ah = _mm256_srli_epi64(a, 32);
    auto bh = _mm256_srli_epi64(b, 32);
    auto lh = _mm256_mul_epu32(a, bh);
    auto hl = _mm256_mul_epu32(ah, b);
    auto hh = _mm256_mul_epu32(ah, bh);
    auto s2 = _mm256_add_epi64(hl, _mm256_and_si256(lh, LOWER32BITS));
    auto s3 = _mm256_add_epi64(hh, _mm256_srli_epi64(lh, 32));

    return _mm256_add_epi64(s3, _mm256_srli_epi64(s2, 32));
}

// Return one of {hi(a * b), hi(a * b) - 1, hi(a * b) - 2}.
// Perform approximate computation of high bits, as described on page 7 of
// https://arxiv.org/pdf/2003.04510.pdf
inline __m256i mul64To128HiApprox2(__m256i a, __m256i b) {
    auto ah = _mm256_srli_epi64(a, 32);
    auto bh = _mm256_srli_epi64(b, 32);
    auto lh = _mm256_mul_epu32(a, bh);
    auto hl = _mm256_mul_epu32(ah, b);
    auto hh = _mm256_mul_epu32(ah, bh);
    auto s1 = _mm256_srli_epi64(lh, 32);
    auto s2 = _mm256_srli_epi64(hl, 32);

    return _mm256_add_epi64(hh, _mm256_add_epi64(s1, s2));
}

inline __m256i mulModLazy(const __m256i x, const __m256i y,
                          const __m256i y_barrett, const __m256i mod) {
    __m256i q = arith::mul64To128Hi(x, y_barrett);
    return _mm256_sub_epi64(arith::mul64To128Lo(y, x),
                            arith::mul64To128Lo(q, mod));
}

// the result is in [0, 4 * mod)
inline __m256i reduceBarrettLazy(const __m256i op, const __m256i barr,
                                 const __m256i mod) {
    __m256i quot = arith::mul64To128HiApprox2(op, barr);
    __m256i prod = arith::mul64To128Lo(quot, mod);
    __m256i res = _mm256_sub_epi64(op, prod);
    return res;
}

inline __m256i load256(const hem::u64 *op, hem::u64 idx) {
    return _mm256_loadu_si256(reinterpret_cast<const __m256i *>(op + idx));
}

inline void store256(hem::u64 *res, hem::u64 idx, __m256i res_vec) {
    _mm256_storeu_si256(reinterpret_cast<__m256i *>(res + idx), res_vec);
}

inline __m256i mm256Set1Epi64x(const hem::u64 value) {
    return _mm256_set1_epi64x(static_cast<long long>(value));
}

inline __m256i mm256HexlShrdiEpi64(__m256i x, __m256i y, int bit_shift) {
    auto c_lo = _mm256_srli_epi64(x, bit_shift);
    auto c_hi = _mm256_slli_epi64(y, 64 - bit_shift);
    return _mm256_or_si256(c_lo, c_hi);
}

template <bool AddToResult>
inline void singleMultModAVX256Int(__m256i &res, __m256i op1, __m256i op2,
                                   __m256i v_barr, int k_1, __m256i v_modulus,
                                   __m256i v_twice_mod) {
    __m256i res_tmp;
    if constexpr (AddToResult)
        res_tmp = res;

    __m256i vprod_hi, vprod_lo;
    arith::mul64To128(op1, op2, vprod_hi, vprod_lo);
    __m256i c1 = mm256HexlShrdiEpi64(vprod_lo, vprod_hi, k_1);
    __m256i c3 = arith::mul64To128HiApprox2(c1, v_barr);
    res = arith::mul64To128Lo(c3, v_modulus);
    res = _mm256_sub_epi64(vprod_lo, res);
    res = arith::subIfGE(res, v_twice_mod);
    res = arith::subIfGE(res, v_modulus);

    if constexpr (AddToResult) {
        res = _mm256_add_epi64(res, res_tmp);
        res = arith::subIfGE(res, v_modulus);
    } else {
        (void)(res_tmp);
    }
}

} // namespace HEaaN::arith
