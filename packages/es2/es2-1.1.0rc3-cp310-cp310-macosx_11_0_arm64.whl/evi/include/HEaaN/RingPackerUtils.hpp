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

#include "LWE/Context.hpp"
#include "LWE/SecretKey.hpp"
#include "SecretKey.hpp"

namespace HEaaN {

/// @brief get the number of output ciphertexts after decompose
/// @param context_from context of the input ciphertext
/// @param context_to context of the output ciphertexts
/// @details the returned value equals to the ratio of degrees of the two
/// contexts
HEAAN_API u64 getNumCiphertextsAfterFullDecompose(const Context &context_from,
                                                  const Context &context_to);

/// @brief get the number of input ciphertext to compose
/// @param context_from context of the input ciphertexts
/// @param context_to context of the output ciphertext
/// @details the returned value equals to the ratio of degrees of the two
/// contexts
HEAAN_API u64 getNumCiphertextsToFullCompose(const Context &context_from,
                                             const Context &context_to);

/// @brief get the number of output ciphertexts after unpack
/// @param context_from context of the input ciphertext
/// @details the returned value equals to the degree of the context
HEAAN_API u64 getNumCiphertextsAfterUnPack(const Context &context_from);

/// @brief generate secret key which encrypts LWE ciphertexts which are resulted
/// by unpacking a RLWE ciphertext
/// @param lwe_context The context to be used to generate LWE secret key
/// @param sk The secret key which encrypts the RLWE ciphertext which will be
/// unpacked
HEAAN_API LWE::SecretKey
genLWESecretKeyAfterUnPack(const LWE::Context &lwe_context,
                           const SecretKey &sk);

HEAAN_API MLWESecretKey genMLWESecretKeyAfterUnPack(const Context &mlwe_context,
                                                    const SecretKey &sk);

template <EncryptionType enc_type>
HEAAN_API SecretKeyBase<enc_type>
genEmbedSecretKey(const Context &context_emb,
                  const SecretKeyBase<enc_type> &sk);

template <EncryptionType enc_type>
HEAAN_API SecretKeyBase<enc_type>
genConjInvSecretKey(const Context &context_ci,
                    const SecretKeyBase<enc_type> &sk);

/// @brief get the number of input ciphertext to perform modPack
/// @param context_from context of the input ciphertexts
/// @param context_to context of the output ciphertext
/// @details the returned value equals to the ratio of degrees of the two
/// contexts
HEAAN_API u64 getNumCiphertextsToModPack(const Context &context_from,
                                         const Context &context_to);

HEAAN_API u64 getNumCiphertextsToModPack(const LWE::Context &context_from,
                                         const Context &context_to);

HEAAN_API Real computeModulusSwitchCompensation(const Context &context_from,
                                                const Context &context_to,
                                                u64 level_from, u64 level_to);

} // namespace HEaaN
