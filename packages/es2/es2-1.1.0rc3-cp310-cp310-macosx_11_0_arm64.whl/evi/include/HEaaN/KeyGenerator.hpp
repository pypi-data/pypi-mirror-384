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

#include <memory>
#include <optional>
#include <string>

#include "HEaaN/Context.hpp"
#include "HEaaN/HEaaNExport.hpp"
#include "HEaaN/IncreaseNSKeyBundle.hpp"
#include "HEaaN/KeyPack.hpp"
#include "HEaaN/LWE/SecretKey.hpp"
#include "HEaaN/MStoSSKeyBundle.hpp"
#include "HEaaN/ModPackKeyBundle.hpp"
#include "HEaaN/MultiSecretSwitchKeyBundle.hpp"
#include "HEaaN/RingSwitchKey.hpp"
#include "HEaaN/SStoMSBisectionKeyBundle.hpp"
#include "HEaaN/SStoMSKeyBundle.hpp"
#include "HEaaN/SecretKey.hpp"

namespace HEaaN {

class KeyGeneratorImpl;

///
///@brief A class generating public (encryption/evaluation) keys from a
/// secret key
///
class HEAAN_API KeyGenerator {
public:
    ///@brief Create a KeyGenerator object
    ///@details This generator internally creates a KeyPack object, which the
    /// user can later extract by `getKeyPack()` function. The SecretKey sk
    /// should have the same context as the input context. Otherwise,
    /// throws RuntimeException.
    explicit KeyGenerator(const Context &context, const SecretKey &sk);

    ///@brief Create a KeyGenerator object from an existing KeyPack object.
    ///@details The SecretKey sk should have the same context as the input
    /// context. Otherwise, throws RuntimeException.
    explicit KeyGenerator(const Context &context, const SecretKey &sk,
                          const KeyPack &pack);
    explicit KeyGenerator(const Context &context, const MSRLWESecretKey &sk,
                          const KeyPack &pack);
    ///@brief Create a KeyGenerator object which can generate key that can
    /// perform sparse secret encapsulation, with the same parameter which @p
    /// context is constructed for.
    ///@throws RuntimeException if @p context_sparse is not a context
    /// constructed with the corresponding sparse parameter of which constructed
    /// context.
    /// Please refer to getSparseParameterPresetFor() for the sparse parameters.
    explicit KeyGenerator(const Context &context, const Context &context_sparse,
                          const SecretKey &sk);

    ///@brief Create a KeyGenerator object from an existing @p pack object which
    /// can generate key that can which can perform sparse secret encapsulation,
    /// with the same parameter which context is constructed for.
    ///@throws RuntimeException if @p context_sparse is not a context
    /// constructed with the corresponding sparse parameter of @p context.
    /// Please refer to getSparseParameterPresetFor() for the sparse parameters.
    explicit KeyGenerator(const Context &context, const Context &context_sparse,
                          const SecretKey &sk, const KeyPack &pack);
    explicit KeyGenerator(const Context &context, const Context &context_sparse,
                          const MSRLWESecretKey &sk, const KeyPack &pack);
    /// @brief Create a KeyGenerator object without a SecretKey in order to
    /// generate specific keys without a default SecretKey
    /// @details Currently, only ModPackKeyBundles could be generated without
    /// a default SecretKey
    explicit KeyGenerator(const Context &context);

    //////////////////////////////////
    // Functions for key generation //
    //////////////////////////////////

    ///@brief Generate an encryption key into the internal `KeyPack` object
    void genEncKey(void) const;

    ///@brief Generate a multiplication key into the internal `KeyPack` object
    void genMultKey(void) const;

    ///@brief Generate a conjugation key into the internal `KeyPack` object
    void genConjKey(void) const;

    ///@brief Generate a rotation key for the left rotation with `rot` steps,
    /// into the internal KeyPack object.
    void genLeftRotKey(u64 rot) const;

    ///@brief Generate a rotation key for the right rotation with `rot` steps,
    /// into the internal KeyPack object.
    void genRightRotKey(u64 rot) const;

    ///@brief Generate a bundle of rotation keys
    ///@details This function creates rotations keys for the left and right
    /// rotations with all power-of-two steps, so that any arbitrary rotation
    /// can be decomposed as a composition of these base rotations.
    void genRotKeyBundle(void) const;

    void genFuseRotKeyBundle(void) const;
    void genFuseRotKeyBundleWithSSE(void) const;

    ///@brief Generate an encryption key into the internal `KeyPack` object
    ///@deprecated This function is deprecated in favor of `genEncKey()` for
    /// consistency of function names. It will be removed in a future release.
    [[deprecated("Use genEncKey() instead")]] void
    genEncryptionKey(void) const {
        genEncKey();
    }

    ///@brief Generate a multiplication key into the internal `KeyPack` object
    ///@deprecated This function is deprecated in favor of `genMultKey()` for
    /// consistency of function names. It will be removed in a future release.
    [[deprecated("Use genMultKey() instead")]] void
    genMultiplicationKey(void) const {
        genMultKey();
    }

    ///@brief Generate a conjugation key into the internal `KeyPack` object
    ///@deprecated This function is deprecated in favor of `genConjKey()` for
    /// consistency of function names. It will be removed in a future release.
    [[deprecated("Use genConjKey() instead")]] void
    genConjugationKey(void) const {
        genConjKey();
    }

    ///@brief Generate a rotation key for the left rotation with `rot` steps,
    /// into the internal KeyPack object.
    ///@deprecated This function is deprecated in favor of `genLeftRotKey()` for
    /// consistency of function names. It will be removed in a future release.
    [[deprecated("Use genLeftRotKey() instead")]] void
    genLeftRotationKey(u64 rot) const {
        genLeftRotKey(rot);
    }

    ///@brief Generate a rotation key for the right rotation with `rot` steps,
    /// into the internal KeyPack object.
    ///@deprecated This function is deprecated in favor of `genRightRotKey()`
    /// for consistency of function names. It will be removed in a future
    /// release.
    [[deprecated("Use genRightRotKey() instead")]] void
    genRightRotationKey(u64 rot) const {
        genRightRotKey(rot);
    }

    ///@brief Generate a bundle of rotation keys
    ///@details This function creates rotations keys for the left and right
    /// rotations with all power-of-two steps, so that any arbitrary rotation
    /// can be decomposed as a composition of these base rotations.
    ///@deprecated This function is deprecated in favor of `genRotKeyBundle()`
    /// for consistency of function names. It will be removed in a future
    /// release.
    [[deprecated("Use genRotKeyBundle() instead")]] void
    genRotationKeyBundle(void) const {
        genRotKeyBundle();
    }

    ///@brief Generate a pair of keys for sparse secret encapsulation
    ///@details This function creates switching keys between the dense secret
    /// key and the sparse secret key so the sparse secret encapsulation can be
    /// performed during bootstrapping.
    ///@throws RuntimeException
    void genSparseSecretEncapsulationKey(void) const;

    template <EncryptionType enc_type>
    MultiSecretSwitchKeyBundle genMultiSecretSwitchKeyBundle(
        const SecretKeyBase<enc_type> &sk_ss,
        const std::vector<MSRLWESecretKey> &sk_ms_vec) const;

    template <EncryptionType enc_type>
    MultiSecretSwitchKeyBundle
    genMultiSecretSwitchKeyBundle(const SecretKeyBase<enc_type> &sk_ss,
                                  const std::vector<MSRLWESecretKey> &sk_ms_vec,
                                  const SecretKeyBase<enc_type> &sk_real_ss,
                                  const MSRLWESecretKey &sk_real_ms) const;

    template <EncryptionType enc_type>
    SStoMSBisectionKeyBundle genSStoMSBisectionKeyBundle(
        const SecretKeyBase<enc_type> &sk_ss,
        const std::vector<MSRLWESecretKey> &sk_ms_vec) const;

    ///@brief Generate commonly used keys
    ///@details Be cautious that for bigger parameter sets, this function
    /// creates a lot of public keys in the internal KeyPack object, causing a
    /// high memory usage.  In order to prevent this, the user might want to not
    /// use this function directly, and do use other key generation functions in
    /// the class separately, and use `save()` and `flush()` between the key
    /// generation.
    inline void genCommonKeys(void) const {
        genEncKey();
        genMultKey();
        genConjKey();
        genRotKeyBundle();
    }

    ///@brief Generate rotation keys used for accelerating the bootstrapping
    /// process.
    ///@param[in] log_slots
    ///@param[in] use_min_keys Whether or not to use minimal rotation keys for
    /// bootstrap
    ///@details This function generates only rotation keys. Bootstrapping
    /// process requires multiplication key and conjugation key, which are not
    /// generated in this function.
    void genRotKeysForBootstrap(const u64 log_slots,
                                bool use_min_keys = false) const;
    void genRotKeysForBootstrap(const std::vector<u64> &log_dft_sizes,
                                bool use_min_keys = false) const;

    /// @brief Generate keys for ModPack for ciphertexts given secret keys of
    /// input and output ciphertexts.
    /// @tparam enc_type_to the encryption type of output ciphertext.
    /// @param[in] sk_from the secret key which have encrypted the input
    /// ciphertext(s)
    /// @param[in] sk_to the secret key which have encrypted the output
    /// ciphertext
    /// @returns A ModPackKeyBundle object which owns the generated packing keys
    /// @details The number of switching keys in the generated bundle equals to
    /// (sk_from.rank) / (sk_to.rank).
    /// @details The generated ModPackKeyBundle can be used to pack
    /// (sk_to.degree) / (sk_from.degree) ciphertexts, encrypted with sk_from,
    /// to a single ciphertext encrypted with sk_to.
    /// @throws RuntimeException if sk_to.degree * sk_to.rank is not
    /// equal to the degree of the ring of current RLWE encryption
    /// @throws RuntimeException if sk_from.degree does not divide sk_to.degree
    /// @throws RuntimeException if sk_to.rank does not divide sk_from.rank
    template <EncryptionType enc_type_to>
    ModPackKeyBundle
    genModPackKeyBundle(const MLWESecretKey &sk_from,
                        const SecretKeyBase<enc_type_to> &sk_to) const;

    /// @brief Generate keys for ModPack for ciphertexts given secret keys of
    /// input and output ciphertexts.
    /// @tparam enc_type_to the encryption type of output ciphertext.
    /// @param[in] sk_from the secret key which have encrypted the input
    /// ciphertext(s)
    /// @param[in] sk_to the secret key which have encrypted the output
    /// ciphertext
    /// @returns A ModPackKeyBundle object which owns the generated packing keys
    /// @details The number of switching keys in the generated bundle equals to
    /// (sk_from.dimension) / (sk_to.rank).
    /// @details The generated ModPackKeyBundle can be used to pack
    /// (sk_to.degree) LWE ciphertexts, encrypted with sk_from,
    /// to a single ciphertext encrypted with sk_to.
    /// @throws RuntimeException if sk_to.degree * sk_to.rank is not
    /// equal to the degree of the ring of current RLWE encryption
    /// @throws RuntimeException if sk_to.rank does not divide
    /// sk_from.dimension
    template <EncryptionType enc_type_to>
    ModPackKeyBundle
    genModPackKeyBundle(const LWE::SecretKey &sk_from,
                        const SecretKeyBase<enc_type_to> &sk_to) const;

    template <EncryptionType enc_type_to>
    MStoSSKeyBundle
    genMStoSSKeyBundle(const MSRLWESecretKey &sk_from,
                       const SecretKeyBase<enc_type_to> &sk_to) const;

    template <EncryptionType enc_type_to>
    SStoMSKeyBundle
    genSStoMSKeyBundle(const SecretKeyBase<enc_type_to> &sk_from,
                       const MSRLWESecretKey &sk_to) const;

    IncreaseNSKeyBundle
    genIncreaseNSKeyBundle(const MSRLWESecretKey &sk_from,
                           const MSRLWESecretKey &sk_to) const;

    /// @brief Generate key to decompose a ciphertext given secret key of
    /// output ciphertexts.
    /// @param[in] context_swk Context object to generate switch key with
    /// @param[in] sk_to the secret key which have encrypted the output
    /// ciphertexts
    /// @returns A RingSwitchKey object which can be used to decompose a
    /// ciphertext
    /// @details The generated RingSwitchKey can be used to decompose a
    /// ciphertext, encrypted with the secret key initialized in the KeyPack, to
    /// (sk.degree / sk_to.degree ) ciphertexts encrypted with @p sk_to.
    /// @p context_swk should be a context constructed with a parameter
    /// dedicated to the generation of decompose key. The parameter uses same
    /// modulus bits and hamming weight to the parameter decomposing to, but is
    /// constructed over the ring of the parameter decomposing from.
    /// @throws RuntimeException if sk_to.degree does not divide the degree of
    /// the ring of current RLWE encryption
    RingSwitchKey genDecomposeKey(const Context &context_swk,
                                  const SecretKey &sk_to) const;

    /// @brief Generate key to compose a ciphertext given secret key of
    /// input ciphertexts.
    /// @param[in] sk_from the secret key which have encrypted the input
    /// ciphertext
    /// @returns A RingSwitchKey object which can be used to compose a
    /// ciphertext
    /// @details The generated RingSwitchKey can be used to compose (sk.degree /
    /// sk_from.degree ) ciphertexts encrypted with @p sk_from, to a ciphertext
    /// encrypted with the secret key initialized in the KeyPack
    /// @throws RuntimeException if sk_from.degree does not divide the degree of
    /// the ring of current RLWE encryption
    RingSwitchKey genComposeKey(const SecretKey &sk_from) const;

    RingSwitchKey genSwitchKey(const SecretKey &sk_from,
                               const SecretKey &sk_to) const;
    RingSwitchKey genSwitchKeyMSRLWE(const MSRLWESecretKey &sk_from,
                                     const MSRLWESecretKey &sk_to) const;
    ///////////////////////
    // Utility functions //
    ///////////////////////

    ///@brief Save the generated keys in the internal KeyPack object into files.
    ///@param[in] dir_path must indicate a valid directory.
    ///@details This function creates a subdirectory `PK/` inside `dirPath`
    /// directory, and save all the keys in the cache of the KeyPack object into
    /// this subdirectory.
    void save(const std::string &dir_path) const;

    ///@brief Discard current internal KeyPack object
    void flush(void);

    ///@brief Extract the internal KeyPack object
    ///@details Keys might be generated again into the keypack after this getter
    /// function is called.
    KeyPack getKeyPack() const { return pack_; }

private:
    const Context context_;
    const std::optional<Context> context_sparse_;

    ///@brief The internal keypack object.
    KeyPack pack_;

    std::shared_ptr<KeyGeneratorImpl> impl_;
};
} // namespace HEaaN
