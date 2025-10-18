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
inline __m512i subIfGE(__m512i a, __m512i b) {
    return _mm512_mask_sub_epi64(a, _mm512_cmpge_epu64_mask(a, b), a, b);
}

inline void mul64To128(__m512i a, __m512i b, __m512i &hi, __m512i &lo) {
    static const __m512i LOWER32BITS = _mm512_set1_epi64(U64C(0xFFFFFFFF));
    auto ah = _mm512_srli_epi64(a, 32);
    auto bh = _mm512_srli_epi64(b, 32);
    auto ll = _mm512_mul_epu32(a, b);
    auto lh = _mm512_mul_epu32(a, bh);
    auto hl = _mm512_mul_epu32(ah, b);
    auto hh = _mm512_mul_epu32(ah, bh);

    auto s1 = _mm512_add_epi64(lh, _mm512_srli_epi64(ll, 32));
    auto s2 = _mm512_add_epi64(hl, _mm512_and_si512(s1, LOWER32BITS));
    auto s3 = _mm512_add_epi64(hh, _mm512_srli_epi64(s1, 32));

    hi = _mm512_add_epi64(s3, _mm512_srli_epi64(s2, 32));
    lo = _mm512_or_si512(_mm512_slli_epi64(s2, 32),
                         _mm512_and_si512(ll, LOWER32BITS));
}

inline __m512i mul64To128Lo(__m512i a, __m512i b) {
    return _mm512_mullo_epi64(a, b);
}

inline __m512i mul64To128Hi(__m512i a, __m512i b) {
    static const __m512i LOWER32BITS = _mm512_set1_epi64(U64C(0xFFFFFFFF));
    auto ah = _mm512_srli_epi64(a, 32);
    auto bh = _mm512_srli_epi64(b, 32);
    auto ll = _mm512_mul_epu32(a, b);
    auto lh = _mm512_mul_epu32(a, bh);
    auto hl = _mm512_mul_epu32(ah, b);
    auto hh = _mm512_mul_epu32(ah, bh);

    auto s1 = _mm512_add_epi64(lh, _mm512_srli_epi64(ll, 32));
    auto s2 = _mm512_add_epi64(hl, _mm512_and_si512(s1, LOWER32BITS));
    auto s3 = _mm512_add_epi64(hh, _mm512_srli_epi64(s1, 32));

    return _mm512_add_epi64(s3, _mm512_srli_epi64(s2, 32));
}

// Return one of {hi(a * b), hi(a * b) - 1, hi(a * b) - 2}.
// Perform approximate computation of high bits, as described on page 7 of
// https://arxiv.org/pdf/2003.04510.pdf
inline __m512i mul64To128HiApprox2(__m512i a, __m512i b) {
    auto ah = _mm512_srli_epi64(a, 32);
    auto bh = _mm512_srli_epi64(b, 32);
    auto lh = _mm512_mul_epu32(a, bh);
    auto hl = _mm512_mul_epu32(ah, b);
    auto hh = _mm512_mul_epu32(ah, bh);
    auto s1 = _mm512_srli_epi64(lh, 32);
    auto s2 = _mm512_srli_epi64(hl, 32);

    return _mm512_add_epi64(hh, _mm512_add_epi64(s1, s2));
}

inline __m512i mulModLazy(const __m512i x, const __m512i y,
                          const __m512i y_barrett, const __m512i mod) {
    __m512i q = arith::mul64To128Hi(x, y_barrett);
    return _mm512_sub_epi64(arith::mul64To128Lo(y, x),
                            arith::mul64To128Lo(q, mod));
}

// the result is in [0, 4 * mod)
inline __m512i reduceBarrettLazy(const __m512i op, const __m512i barr,
                                 const __m512i mod) {
    __m512i quot = arith::mul64To128HiApprox2(op, barr);
    __m512i prod = _mm512_mullo_epi64(quot, mod);
    __m512i res = _mm512_sub_epi64(op, prod);
    return res;
}

inline __m512i load512(const hem::u64 *op, hem::u64 idx) {
    return _mm512_loadu_si512(reinterpret_cast<const __m512i *>(op + idx));
}

inline void store512(hem::u64 *res, hem::u64 idx, __m512i res_vec) {
    _mm512_storeu_si512(reinterpret_cast<__m512i *>(res + idx), res_vec);
}

inline __m512i mm512Set1Epi64(const hem::u64 value) {
    return _mm512_set1_epi64(static_cast<long long>(value));
}

inline __m512i mm512HexlShrdiEpi64(__m512i x, __m512i y, int bit_shift) {
    __m512i c_lo = _mm512_srli_epi64(x, bit_shift);
    __m512i c_hi = _mm512_slli_epi64(y, 64 - bit_shift);
    return _mm512_add_epi64(c_lo, c_hi);
}

template <bool AddToResult>
inline void singleMultModAVX512Float(__m512i &res, __m512i op1, __m512i op2,
                                     __m512d v_u, __m512d v_p,
                                     __m512i v_modulus) {
    constexpr int ROUND_MODE = (_MM_FROUND_TO_POS_INF | _MM_FROUND_NO_EXC);

    __m512i res_tmp;
    if constexpr (AddToResult)
        res_tmp = res;

    auto v_x = _mm512_cvt_roundepu64_pd(op1, ROUND_MODE);
    auto v_y = _mm512_cvt_roundepu64_pd(op2, ROUND_MODE);
    __m512d v_h = _mm512_mul_pd(v_x, v_y);
    __m512d v_l = _mm512_fmsub_pd(v_x, v_y, v_h);
    __m512d v_b = _mm512_mul_pd(v_h, v_u);
    __m512d v_c = _mm512_floor_pd(v_b);
    __m512d v_d = _mm512_fnmadd_pd(v_c, v_p, v_h); // NOLINT
    __m512d v_g = _mm512_add_pd(v_d, v_l);

    auto mask = _mm512_cmp_pd_mask(v_g, _mm512_setzero_pd(), _CMP_LT_OQ);
    v_g = _mm512_mask_add_pd(v_g, mask, v_g, v_p);
    res = _mm512_cvt_roundpd_epu64(v_g, ROUND_MODE);

    if constexpr (AddToResult) {
        res = _mm512_add_epi64(res, res_tmp);
        res = arith::subIfGE(res, v_modulus);
    } else {
        // to avoid warning error
        (void)(v_modulus);
        (void)(res_tmp);
    }
}

template <bool AddToResult>
inline void singleMultModAVX512Int(__m512i &res, __m512i op1, __m512i op2,
                                   __m512i v_barr, int k_1, __m512i v_modulus,
                                   __m512i v_twice_mod) {
    __m512i res_tmp;
    if constexpr (AddToResult)
        res_tmp = res;

    __m512i vprod_hi, vprod_lo;
    arith::mul64To128(op1, op2, vprod_hi, vprod_lo);
    __m512i c1 = mm512HexlShrdiEpi64(vprod_lo, vprod_hi, k_1);
    __m512i c3 = arith::mul64To128HiApprox2(c1, v_barr);
    res = _mm512_mullo_epi64(c3, v_modulus);
    res = _mm512_sub_epi64(vprod_lo, res);
    res = arith::subIfGE(res, v_twice_mod);
    res = arith::subIfGE(res, v_modulus);

    if constexpr (AddToResult) {
        res = _mm512_add_epi64(res, res_tmp);
        res = arith::subIfGE(res, v_modulus);
    } else {
        // to avoid warning error
        (void)(res_tmp);
    }
}

} // namespace HEaaN::arith
