////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once
// TODO: Remove this file and use the original file from HEAAN library.
// This file is a copy of the original file from HEAAN library.
// The original file is located at HEAAN/src/NTT.cpp

#if defined(HEM_AVX2) || defined(HEM_AVX512DQ)
#include <immintrin.h>
#endif // HEM_AVX2 || HEM_AVX512DQ

#include "hem/DataType.hpp"
#include "hem/RawArray.hpp"
#include "hem/device/Device.hpp"

namespace HEaaN::NTT {

enum class NttType : int {
    NEGACYCLIC,            // X^N + 1
    NEGACYCLIC_COMPATIBLE, // X^N + 1, compatible with X^2N + 1
    CYCLIC,                // X^N - 1, comptible with X^2N + 1
    NONE
};

class NTT {
public:
    NTT(hem::u64 degree, hem::u64 modulus, hem::Device device,
        NttType ntt_type = NttType::NEGACYCLIC);

    template <int OutputModFactor = 1> // possible value: 1, 2, 4
    void computeForward(hem::u64 *op) const;

    template <int OutputModFactor = 1> // possible value: 1, 2
    void computeBackward(hem::u64 *op) const;

#ifdef HEM_AVX2
    template <int OutputModFactor = 1> // possible value: 1, 2, 4
    void computeForwardAVX256(hem::u64 *op) const;

    template <int OutputModFactor = 1> // possible value: 1, 2
    void computeBackwardAVX256(hem::u64 *op) const;
#endif // HEM_AVX2

#ifdef HEM_AVX512DQ
    template <int OutputModFactor = 1> // possible value: 1, 2, 4
    void computeForwardAVX512DQ(hem::u64 *op) const;

    template <int OutputModFactor = 1> // possible value: 1, 2
    void computeBackwardAVX512DQ(hem::u64 *op) const;

    void conversionAVX512DQ(const hem::u64 *op, hem::u64 *res) const;
    void inversionAVX512DQ(const hem::u64 *op, hem::u64 *res) const;
#endif // HEM_AVX512DQ

    // Z[X + X^(-1)]/<X^2N + 1>  ->  Z[X]/<X^N - 1>
    void conversion(const hem::u64 *op, hem::u64 *res) const;

    // Z[X]/<X^N - 1>  ->  Z[X + X^(-1)]/<X^2N + 1>
    void inversion(const hem::u64 *op, hem::u64 *res) const;

    template <int OutputModFactor = 1>
    void execNttBatch(const hem::u64 *op, hem::u64 *res,
                      const hem::u64 num_poly) const;

    template <int OutputModFactor = 1>
    void execiNttBatch(const hem::u64 *op, hem::u64 *res,
                       const hem::u64 num_poly) const;

    hem::RawArray<hem::u64>
    RevertOrder(const hem::RawArray<hem::u64> &src) const {
        hem::RawArray<hem::u64> temp(hem::DeviceType::CPU, src.size());
        const hem::u64 *curr_ptr = src.data() + 1;
        for (hem::u64 size_to_copy = degree_ / 2; size_to_copy > 0;
             size_to_copy /= 2) {
            hem::u64 *dst = temp.data() + size_to_copy;
            std::copy_n(curr_ptr, size_to_copy, dst);
            curr_ptr += size_to_copy;
        }
        return temp;
    };

private:
    hem::u64 modulus_;
    hem::u64 two_modulus_;
    hem::u64 degree_;
    NttType ntt_type_;

    hem::u64 barr_for_64_;
    hem::u64 two_to_64_;
    hem::u64 two_to_64_shoup_;

    // roots of unity (bit reversed)
    hem::RawArray<hem::u64> psi_rev_;
    hem::RawArray<hem::u64> psi_inv_rev_;
    hem::RawArray<hem::u64> psi_rev_shoup_;
    hem::RawArray<hem::u64> psi_inv_rev_shoup_;

    // conversion for Real HEaaN
    // [1, w, w^2, w^3, ... ] where w is primitive 4N-th root of unity
    hem::RawArray<hem::u64> roots_;
    hem::RawArray<hem::u64> roots_inv_;
    hem::RawArray<hem::u64> roots_shoup_;
    hem::RawArray<hem::u64> roots_inv_shoup_;

    // variables for last step of backward NTT
    hem::u64 degree_inv_;
    hem::u64 degree_inv_barrett_;
    hem::u64 degree_inv_w_;
    hem::u64 degree_inv_w_barrett_;

    void computeForwardNativeSingleStep(hem::u64 *op, const hem::u64 t) const;
    void computeBackwardNativeSingleStep(hem::u64 *op, const hem::u64 t) const;
    void computeBackwardNativeLast(hem::u64 *op) const;

#ifdef HEM_AVX512DQ
    void initAVX512Constants();

    __m512i two_modulus_avx_512_;
    __m512i modulus_avx_512_;
    __m512i degree_inv_avx_512_;
    __m512i degree_inv_barrett_avx_512_;
    __m512i degree_inv_w_avx_512_;
    __m512i degree_inv_w_barrett_avx_512_;

    // psi_rev data for AVX512 when t = 1, 2
    hem::RawArray<hem::u64> psi_rev_avx_512_t1_;
    hem::RawArray<hem::u64> psi_rev_shoup_avx_512_t1_;
    hem::RawArray<hem::u64> psi_inv_rev_avx_512_t1_;
    hem::RawArray<hem::u64> psi_inv_rev_shoup_avx_512_t1_;
    hem::RawArray<hem::u64> psi_rev_avx_512_t2_;
    hem::RawArray<hem::u64> psi_rev_shoup_avx_512_t2_;
    hem::RawArray<hem::u64> psi_inv_rev_avx_512_t2_;
    hem::RawArray<hem::u64> psi_inv_rev_shoup_avx_512_t2_;

    // Single step of forward NTT
    void computeForwardAVX512T1(hem::u64 *op) const;
    void computeForwardAVX512T2(hem::u64 *op) const;
    void computeForwardAVX512T4(hem::u64 *op) const;
    void computeForwardAVX512Tn(hem::u64 *op, const hem::u64 t) const;

    // Single step of backward NTT
    void computeBackwardAVX512T1(hem::u64 *op) const;
    void computeBackwardAVX512T2(hem::u64 *op) const;
    void computeBackwardAVX512T4(hem::u64 *op) const;
    void computeBackwardAVX512Tn(hem::u64 *op, const hem::u64 t) const;
    void computeBackwardAVX512Last(hem::u64 *op) const;
#endif

#ifdef HEM_AVX2
    void initAVX2Constants();

    __m256i two_modulus_avx_256_;
    __m256i modulus_avx_256_;
    __m256i degree_inv_avx_256_;
    __m256i degree_inv_barrett_avx_256_;
    __m256i degree_inv_w_avx_256_;
    __m256i degree_inv_w_barrett_avx_256_;

    // psi_rev data for AVX256 when t = 1
    hem::RawArray<hem::u64> psi_rev_avx_256_t1_;
    hem::RawArray<hem::u64> psi_rev_shoup_avx_256_t1_;
    hem::RawArray<hem::u64> psi_inv_rev_avx_256_t1_;
    hem::RawArray<hem::u64> psi_inv_rev_shoup_avx_256_t1_;

    // Single step of forward NTT
    void computeForwardAVX256T1(hem::u64 *op) const;
    void computeForwardAVX256T2(hem::u64 *op) const;
    void computeForwardAVX256Tn(hem::u64 *op, const hem::u64 t) const;

    // Single step of backward NTT
    void computeBackwardAVX256T1(hem::u64 *op) const;
    void computeBackwardAVX256T2(hem::u64 *op) const;
    void computeBackwardAVX256Tn(hem::u64 *op, const hem::u64 t) const;
    void computeBackwardAVX256Last(hem::u64 *op) const;

    void conversionAVX256(const hem::u64 *op, hem::u64 *res) const;
    void inversionAVX256(const hem::u64 *op, hem::u64 *res) const;
#endif
};

class NTTArray {
public:
    NTTArray() = delete;
    NTTArray(const hem::u64 degree, const std::vector<hem::u64> &moduli,
             const hem::Device &device,
             const NttType ntt_type = NttType::NEGACYCLIC);
    ~NTTArray();

    const NTT &operator[](size_t idx) const { return *(ntts[idx]); }

private:
    std::vector<NTT *> ntts;
};
} // namespace HEaaN::NTT
