////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/ModulusMatrix.hpp"
#include "hem/utils/KeySwitcher.hpp"

namespace hem {

void automorphism(const int *op, int *res, const u64 sig, const u64 degree);

// This function works for op != res only.
void multMonomialCPU(const std::vector<HEaaN::Ciphertext> &op,
                     std::vector<HEaaN::Ciphertext> &res, const u64 power);

// This function works for op != res only.
void multMonomialGPU(const std::vector<HEaaN::Ciphertext> &op,
                     std::vector<HEaaN::Ciphertext> &res, const u64 power);

// This function works for op != res only.
void multMonomialCPU(const CTMatrix<u64> &op, CTMatrix<u64> &res,
                     const u64 power);

// This function works for op != res only.
void multMonomialGPU(const CTMatrix<u64> &op, CTMatrix<u64> &res,
                     const u64 power);

// vector<Ciphertext> version

void transposeCPU(const std::vector<HEaaN::Ciphertext> &ctxt_v,
                  HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                  std::vector<HEaaN::Ciphertext> &ctxt_w);

void ccmmFP64CPU(const std::vector<HEaaN::Ciphertext> &ctxt_u,
                 const std::vector<HEaaN::Ciphertext> &ctxt_v,
                 HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                 HEaaN::RingSwitchKey &mul_key,
                 std::vector<HEaaN::Ciphertext> &ctxt_w);

void transposeGPU(const std::vector<HEaaN::Ciphertext> &ctxt_v,
                  HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                  std::vector<HEaaN::Ciphertext> &ctxt_w);

void ccmmNativeGPU(const std::vector<HEaaN::Ciphertext> &ctxt_u,
                   const std::vector<HEaaN::Ciphertext> &ctxt_v,
                   HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                   HEaaN::RingSwitchKey &mul_key,
                   std::vector<HEaaN::Ciphertext> &ctxt_w);

// CTMatrix version

void transposeCPU(const CTMatrix<u64> &ctxt_v,
                  HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                  CTMatrix<u64> &ctxt_w);

void ccmmFP64CPU(const CTMatrix<u64> &ctxt_u, const CTMatrix<u64> &ctxt_v,
                 HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                 HEaaN::RingSwitchKey &mul_key, CTMatrix<u64> &ctxt_w);

void transposeGPU(const CTMatrix<u64> &ctxt_v,
                  HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                  CTMatrix<u64> &ctxt_w);

void ccmmNativeGPU(const CTMatrix<u64> &ctxt_u, const CTMatrix<u64> &ctxt_v,
                   HEaaN::KeySwitcher::KeySwitcher &keyswitcher,
                   HEaaN::RingSwitchKey &mul_key, CTMatrix<u64> &ctxt_w);

} // namespace hem
