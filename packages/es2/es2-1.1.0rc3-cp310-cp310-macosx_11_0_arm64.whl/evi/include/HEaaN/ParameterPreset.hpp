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

#include "HEaaN/EncryptionType.hpp"
#include "HEaaN/HEaaNExport.hpp"
#include <cstdint>

namespace HEaaN {
///
///@brief Class of Parameter presets.
///@details The first alphabet denotes whether a parameter is full or somewhat
/// homomorphic encryption. Somewhat homomorphic encryption parameters can use
/// only a finite number of multiplications while full homomorphic encryption
/// parameters can use infinitely many multiplications via bootstrapping. The
/// second alphabet denotes the size of log2(N), where N denotes the degree
/// of the base ring. V(Venti), G(Grande), T(Tall), S(Short), D(Demi) represent
/// log2(N) = 17, 16, 15, 14, 13, respectively. For somewhat parameters, a
/// number that comes after these alphabets indicates total available
/// multiplication number.
///
enum class HEAAN_API ParameterPreset : uint32_t {
    FVa, // Depth optimal FV parameter
    FVb, // High precision FV parameter
    FGa, // Precision optimal FG parameter
    FGb, // Depth optimal FG parameter
    FGbMS,
    FGbSSE,
    FGbSSEMS2,
    FGbSSEMS4,
    FGbSSEMS8,
    FGbSSEMS16,
    FFF,
    FFFMS,
    FTa, // Depth optimal FT parameter
    FTb, // Precision optimal FT parameter
    ST19,
    ST14,
    ST11,
    ST8,
    ST7,
    SS7,
    SD3,
    CUSTOM, // Parameter preset used to create custom parameters
    FVc,    // Precision optimal FV parameter
    FX,     // Small bootstrappable parameter for test
    /* Reserved parameters;
    those are for development and should not be used in common use */
    FGd,  // FG parameter for experimental sparse secret encapsulation support
    SGd0, // A zero-depth parameter which uses compatible prime with FGd
    FGbD12NS6L1, // Degree 12, NS 6
    FGbD12NS3L1, // Degree 12, NS 3
    FGbD12NS2L1, // Degree 12, NS 2
    FGbD12NS1L1, // Degree 12, NS 1
    FGbD3R9L0,   // Degree 3, Rank 9
    SGb0,
    SGb0MS2,
    SGb0MS4,
    SGb0MS8,
    SGb0MS16,
    SSS,
    SSSMS,
    FGxCOEFF,
    SGxCOEFF0,
    FTxCOEFF,
    STxCOEFF0,
    SD3D6R2,   // Deg 6 rank 2 parameter that uses same primes to SD3
    FGbL0,     // Deg 16 level 0 parameter that uses same primes to FGb
    FGbD12L0,  // Deg 12 level 0 parameter that uses same primes to FGb
    FGbD9R3L0, // Deg 9 rank 3 level 0 parameter that uses same primes to FGb
    FGbD8R4L0, // Deg 8 rank 4 level 0 parameter that uses same primes to FGb
    FGbD6R6L0, // Deg 6 rank 6 level 0 parameter that uses same primes to FGb
    FGbL7,
    FGbSmall,

    // FG parameter for experimental outsourced batch-bootstrap support
    FGf,
    FGfSmall,
    FGfO,
    FGfO0,
    FGfL7,
    FGfOL7,
    FGfL7Small,
    // FGfL7 based low precision parameter
    FGfL7Low,
    FGfOL7Low,
    FGfL7SmallLow,
    FGfO0Low,
    FGfL0,
    FGfD12L0,

    // FGh for cleaning function
    FGh,
    FGhL0,
    FGhD12L0,

    // FGSa series
    FGSa,
    SGSa0,

    // FGSb series
    FGSb,
    SGSb0,

    // FGSc series
    FGSc,
    SGSc0,

    // FGSd series
    FGSd,
    SGSd0,

    // FGCa series
    FGCa,
    SGCa0,

    FGe,  // FG parameter for experimental outsourced bootstrap support
    FGeO, // FG parameter which uses near-word-size primes, compatible with FGe

    Discrete_G8,
    Discrete_G8_Sparse,

    Discrete_G8A,
    Discrete_G8A_Small,
    Discrete_G8A_OBTS,
    Discrete_G8A_SHE,
    Discrete_G8A_Sparse,
    Discrete_G8A_L0,
    Discrete_G8A_D12L0,
    Discrete_G8A_D9R3L0,

    Discrete_G8B,
    Discrete_G8B_Small,
    Discrete_G8B_OBTS,
    Discrete_G8B_SHE,
    Discrete_G8B_Sparse,

    Discrete_G10,        // Discrete parameter with logN=16 and depth 10.
    Discrete_G10_Sparse, // SSE param for Discrete_G10.

    Discrete_G10A,
    Discrete_G10A_Sparse,

    Discrete_G12,
    Discrete_G12_Sparse,

    ////////////////////////////////////////////////////////////////////////////
    TONIC_BTS,
    TONIC_BTS_SPARSE,
    TONIC_BTS_OUTSOURCE,
    TONIC_BTS_SMALL,
    TONIC_BTS_L0,
    TONIC_BTS_D12L0,

    TONIC_2_BTS,
    TONIC_2_BTS_SPARSE,
    TONIC_2_BTS_OUTSOURCE,
    TONIC_2_BTS_SMALL,
    TONIC_2_BTS_L0,
    TONIC_2_BTS_D12L0,
    TONIC_2_CLEANING,

    TONIC_3_BTS,
    TONIC_3_BTS_SPARSE,
    TONIC_3_BTS_OUTSOURCE,
    TONIC_3_BTS_OUTSOURCE_REAL,
    TONIC_3_BTS_SMALL,
    TONIC_3_BTS_L0,
    TONIC_3_BTS_D12L0,
    TONIC_3_CLEANING,
};

/// @brief Returns the available encryption type of the given parameter preset
/// @param preset
/// @details For a ParameterPreset, only one among the two encryption types,
/// EncryptionType::RLWE and Encryption::MLWE is available. Ciphertexts and
/// SecretKeys are only be able to constructed with the available encryption
/// type by giving it as a template parameter, i.e. Ciphertext<enc_type> and
/// SecretKey<enc_type>.
HEAAN_API EncryptionType getEncryptionType(ParameterPreset preset);

///@brief Returns the parameter preset which is required to perform
/// sparse secret encapsulation on bootstrapping for certain parameters.
///@param preset
///@details The context of the sparse parameter should be constructed
/// and provided to construct modules for the parameters.
/// Sparse Secret Encapsulation is a technique to ease bootstrapping complexity
/// while maintaing homomorphic capacity. For more details, please refer to the
/// paper : <a href="https://eprint.iacr.org/2022/024">Bootstrapping for
/// Approximate Homomorphic Encryption with Negligible Failure-Probability by
/// Using Sparse-Secret Encapsulation</a>
HEAAN_API ParameterPreset getSparseParameterPresetFor(ParameterPreset preset);
HEAAN_API ParameterPreset getMultiSecretParameterPresetFor(
    ParameterPreset preset, const std::uint64_t num_secret);

///@brief Returns the parameter preset which is required to outsource RNS moduli
/// in the process of bootstrapping for certain parameters.
///@param preset
///@details Bootstrapping can be accelerated by using more compact RNS moduli,
/// which is consisted of near-word-size primes. The moduli represents same
/// modulus with smaller size of data, and requires less computation for HE
/// operations compared to original parameter.
HEAAN_API ParameterPreset
getOutsourcingParameterPresetFor(ParameterPreset preset);

HEAAN_API ParameterPreset getSmallParameterPresetFor(ParameterPreset preset);

} // namespace HEaaN
