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
#include "HomEvaluator.hpp"

namespace HEaaN {

HEAAN_API
void evaluatePolynomial(const HomEvaluator &eval, const Ciphertext &ctxt,
                        const std::vector<Complex> &coefficients,
                        Ciphertext &ctxt_out, const Complex multiplier = 1.0,
                        const u64 num_bs = 16);
HEAAN_API
void evaluateConjugateInvariantPolynomial(
    const HomEvaluator &eval, const Ciphertext &ctxt,
    const std::vector<Complex> &coefficients, Ciphertext &ctxt_out,
    const Complex multiplier = 1.0, const u64 num_bs = 16);
} // namespace HEaaN
