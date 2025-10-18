////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2023 Crypto Lab Inc.                                    //
//                                                                            //
// - This file is part of HEaaN homomorphic encryption library.               //
// - HEaaN cannot be copied and/or distributed without the express permission //
//  of Crypto Lab Inc.                                                        //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "HEaaN/HEaaNExport.hpp"
#include <cstdint>

namespace HEaaN::LWE {

///
///@brief Class of Parameter presets.
///@details The first alphabet 'S' points out that the parameters are for
/// somewhat homomorphic encryption, as bootstrapping is not supported for LWE
/// parameters. The second alphabet denotes the size of log2(N), where N denotes
/// the dimension of the ax part of the ciphertexts. V(Venti), G(Grande),
/// T(Tall), S(Short), D(Demi) represent log2(N) = 17, 16, 15, 14, 13,
/// respectively. For somewhat parameters, a number that comes after these
/// alphabets indicates total available multiplication number.
///
enum class HEAAN_API ParameterPreset : uint32_t {
    SS7,
    SD3,
    CUSTOM, // Parameter preset used to create custom parameters
    /* Reserved parameters;
    those are for development and should not be used */
    FGbD12L0, // Dim 12 level 0 parameter that uses same primes to FGb, which is
              // a RLWE parameter
    FGbD12L1,
    Discrete_G8A_LWE
};

} // namespace HEaaN::LWE
