////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/ModulusMatrix.hpp"
#include "hem/utils/Arith.hpp"
#include "hem/utils/KeySwitcher.hpp"

namespace hem::CCMM {

class BitReverseIndex {
public:
    static const u64 *getBitReverseIndex(const u64 degree) {
        auto *instance = getInstance();
        if (instance->degree_ != degree) {
            instance->clear();

            instance->bit_reverse_index_ = new u64[degree];
            instance->degree_ = degree;
            const auto log_degree = static_cast<u64>(std::log2(degree));

            for (u64 i = 0; i < degree; ++i) {
                instance->bit_reverse_index_[i] =
                    HEaaN::arith::bitReverse(i, log_degree);
            }

            int res = std::atexit([]() { getInstance()->clear(); });
            if (res != 0) {
                throw std::runtime_error(
                    "Failed to register the clear bit reverse index.");
            }
        }

        return instance->bit_reverse_index_;
    }

private:
    static BitReverseIndex *getInstance() {
        static BitReverseIndex instance;
        return &instance;
    }

    void clear() {
        if (bit_reverse_index_) {
            delete[] bit_reverse_index_;
            bit_reverse_index_ = nullptr;
        }
    }

    u64 degree_ = 0;
    u64 *bit_reverse_index_;
};

class InverseSigma {
public:
    static const u64 *getInverseSigma(const u64 degree) {
        auto *instance = getInstance();
        if (instance->degree_ != degree) {
            instance->clear();

            instance->inv_sig_ = new u64[degree];
            instance->degree_ = degree;

            for (u64 sig = 0; sig < degree; ++sig) {
                u64 base = (1 - (sig << 1)) & (2 * degree - 1);
                u64 tmp = (sig << 1) & (2 * degree - 1);
                while (tmp) {
                    tmp = (tmp * tmp) & (2 * degree - 1);
                    base = (base * (tmp + 1)) & (2 * degree - 1);
                }
                instance->inv_sig_[sig] = base & (2 * degree - 1);
            }

            int res = std::atexit([]() { getInstance()->clear(); });
            if (res != 0) {
                throw std::runtime_error(
                    "Failed to register the clear inverse sigma.");
            }
        }

        return instance->inv_sig_;
    }

private:
    static InverseSigma *getInstance() {
        static InverseSigma instance;
        return &instance;
    }

    void clear() {
        if (inv_sig_) {
            delete[] inv_sig_;
            inv_sig_ = nullptr;
        }
    }

    u64 degree_ = 0;
    u64 *inv_sig_;
};

// This function works for op != res only.
void automorphismGPU(const u64 *op, u64 *res, const u64 sig, const u64 shift,
                     const u64 degree, const u64 modulus);

// This function works for op != res only.
void forwardTweakGPU(const u64 **op, u64 **res, const u64 degree,
                     const u64 modulus);

// This function works for op != res only.
void forwardTweakGPU(const HEaaN::Context &context,
                     const std::vector<HEaaN::Ciphertext> &op,
                     std::vector<HEaaN::Ciphertext> &res);

// This function works for op != res only.
void forwardTweakGPU(const HEaaN::Context &context, const CTMatrix<u64> &op,
                     CTMatrix<u64> &res);

// This function works for op != res only.
// Caution: the input op can be changed.
void backwardTweakGPU(u64 **op, u64 **res, const u64 degree, const u64 modulus);

// This function works for op != res only.
// Caution: the input op can be changed.
void backwardTweakGPU(const HEaaN::Context &context,
                      std::vector<HEaaN::Ciphertext> &op,
                      std::vector<HEaaN::Ciphertext> &res);

// This function works for op != res only.
// Caution: the input op can be changed.
void backwardTweakGPU(const HEaaN::Context &context, CTMatrix<u64> &op,
                      CTMatrix<u64> &res);

// PPMM
void ppmmModGPU(u64 *w, const u64 *u, const u64 *v, const u64 q, const u64 d1,
                const u64 d2, const u64 d3);

// Half

// This function works for op != res only.
void forwardTweakHalfGPU(const HEaaN::Context &context,
                         const std::vector<HEaaN::Ciphertext> &op,
                         std::vector<HEaaN::Ciphertext> &res);

void transposeHalfGPU(const std::vector<HEaaN::Ciphertext> &ctxt_v,
                      HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                      std::vector<HEaaN::Ciphertext> &ctxt_w);

// This function works for op != res only.
void forwardTweakHalfGPU(const HEaaN::Context &context, const CTMatrix<u64> &op,
                         CTMatrix<u64> &res);

void transposeHalfGPU(const CTMatrix<u64> &ctxt_v,
                      HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                      CTMatrix<u64> &ctxt_w);

// This function works for op != res only.
void automorphismCPU(const u64 *op, u64 *res, const u64 sig, const u64 shift,
                     const u64 degree, const u64 modulus);

// This function works for op != res only.
void multMonomialCPU(const u64 *op, u64 *res, const u64 degree, const u64 power,
                     const u64 modulus);

// This function works for op != res only.
void multMonomialCPU(const HEaaN::Context &context, const HEaaN::Ciphertext &op,
                     HEaaN::Ciphertext &res, const u64 power);

// This function works for op != res and res == 0 only.
void tweakHelperCPU(const HEaaN::Context &context,
                    const std::vector<HEaaN::Ciphertext> &op,
                    std::vector<HEaaN::Ciphertext> &res, const u64 num);

// This function works for op != res only.
void forwardTweakCPU(const u64 **op, u64 **res, const u64 degree,
                     const u64 modulus);

// This function works for op != res only.
void forwardTweakCPU(const HEaaN::Context &context,
                     const std::vector<HEaaN::Ciphertext> &op,
                     std::vector<HEaaN::Ciphertext> &res);

// This function works for op != res only.
void forwardTweakCPU(const HEaaN::Context &context, const CTMatrix<u64> &op,
                     CTMatrix<u64> &res);

// This function works for op != res only.
// Caution: the input op can be changed.
void backwardTweakCPU(u64 **op, u64 **res, const u64 degree, const u64 modulus);

// This function works for op != res only.
// Caution: the input op can be changed.
void backwardTweakCPU(const HEaaN::Context &context,
                      std::vector<HEaaN::Ciphertext> &op,
                      std::vector<HEaaN::Ciphertext> &res);

// This function works for op != res only.
// Caution: the input op can be changed.
void backwardTweakCPU(const HEaaN::Context &context, CTMatrix<u64> &op,
                      CTMatrix<u64> &res);

// PPMM
void ppmmModCPU(u64 *w, const u64 *u, const u64 *v, const u64 q, const u64 d1,
                const u64 d2, const u64 d3);

// Half

// This function works for op != res only.
void forwardTweakHalfCPU(const HEaaN::Context &context,
                         const std::vector<HEaaN::Ciphertext> &op,
                         std::vector<HEaaN::Ciphertext> &res);

void transposeHalfCPU(const std::vector<HEaaN::Ciphertext> &ctxt_v,
                      HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                      std::vector<HEaaN::Ciphertext> &ctxt_w);

// This function works for op != res only.
void forwardTweakHalfCPU(const HEaaN::Context &context, const CTMatrix<u64> &op,
                         CTMatrix<u64> &res);

void transposeHalfCPU(const CTMatrix<u64> &ctxt_v,
                      HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                      CTMatrix<u64> &ctxt_w);

} // namespace hem::CCMM
