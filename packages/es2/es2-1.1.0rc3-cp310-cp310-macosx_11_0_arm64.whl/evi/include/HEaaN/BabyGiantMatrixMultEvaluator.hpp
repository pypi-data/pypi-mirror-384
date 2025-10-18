////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2024 Crypto Lab Inc.                                    //
//                                                                            //
// - This file is part of HEaaN homomorphic encryption library.               //
// - HEaaN cannot be copied and/or distributed without the express permission //
//  of Crypto Lab Inc.                                                        //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once
#include "Ciphertext.hpp"
#include "HomEvaluator.hpp"

namespace HEaaN {

HEAAN_API
void blockMatMul2DBSGS(const HomEvaluator &eval,
                       const std::vector<Ciphertext> &ctxt_in,
                       const std::vector<std::vector<Plaintext>> &kernel,
                       std::vector<Ciphertext> &ctxt_out, size_t bs,
                       size_t radix, size_t gap);

HEAAN_API
void blockMatMul2DBSGS(const HomEvaluator &eval,
                       const std::vector<MSRLWECiphertext> &ctxt_in,
                       const std::vector<std::vector<Plaintext>> &kernel,
                       std::vector<MSRLWECiphertext> &ctxt_out, size_t bs,
                       size_t radix, size_t gap);

HEAAN_API
void blockMatMul1DBSGS(const HomEvaluator &eval, const Ciphertext &ctxt_in,
                       const std::vector<Plaintext> &diags,
                       Ciphertext &ctxt_out, size_t bs, size_t radix,
                       size_t gap);

HEAAN_API
void blockMatMul1DBSGS(const HomEvaluator &eval, const Ciphertext &ctxt_in,
                       const std::vector<Message> &diags, Ciphertext &ctxt_out,
                       size_t bs, size_t radix, size_t gap);
} // namespace HEaaN
