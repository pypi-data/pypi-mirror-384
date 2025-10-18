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

#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Context.hpp"
#include "HEaaN/EncryptionType.hpp"
#include "HEaaN/LWE/Ciphertext.hpp"
#include "HEaaN/ModPackKeyBundle.hpp"
#include "HEaaN/Plaintext.hpp"
#include "HEaaN/RingSwitchKey.hpp"
#include "HEaaN/SecretKey.hpp"

#include "device/Device.hpp"

#include <vector>

namespace HEaaN {

class HEAAN_API RingPacker {
public:
    ///@brief Decompose a ciphertext into lower degree ciphertexts
    ///@param[in] ctxt_from
    ///@param[in] decompose_key
    ///@param[out] ctxt_to
    void decompose(const Ciphertext &ctxt_from,
                   const RingSwitchKey &decompose_key,
                   std::vector<Ciphertext *> &ctxt_to) const;

    ///@brief Compose ciphertexts to a higher degree ciphertext
    ///@param[in] ctxt_from
    ///@param[in] compose_key
    ///@param[out] ctxt_to
    void compose(const std::vector<const Ciphertext *> &ctxt_from,
                 const RingSwitchKey &compose_key, Ciphertext &ctxt_to) const;

    ///@brief Pack MLWE ciphertexts to a single (RLWE/MLWE) ciphertext
    ///@param[in] ctxt_from
    ///@param[in] modpack_keys
    ///@param[out] ctxt_to
    template <EncryptionType enc_type_to>
    void modPack(const std::vector<const MLWECiphertext *> &ctxt_from,
                 const ModPackKeyBundle &modpack_keys,
                 CiphertextBase<enc_type_to> &ctxt_to) const;

    ///@brief Pack LWE ciphertexts to a single (RLWE/MLWE) ciphertext
    ///@param[in] ctxt_from
    ///@param[in] modpack_keys
    ///@param[out] ctxt_to
    template <EncryptionType enc_type_to>
    void modPack(const std::vector<const LWE::Ciphertext *> &ctxt_from,
                 const ModPackKeyBundle &modpack_keys,
                 CiphertextBase<enc_type_to> &ctxt_to) const;

    void unPack(const Ciphertext &ctxt_from,
                const std::vector<MLWECiphertext *> &ctxt_to) const;
    void unPackOneOutput(const Ciphertext &ctxt_from,
                         MLWECiphertext &ctxt_to) const;

    ///@brief Unpack a ciphertext into several LWE ciphertexts
    ///@param[in] ctxt_from
    ///@param[out] ctxt_to
    void unPack(const Ciphertext &ctxt_from,
                const std::vector<LWE::Ciphertext *> &ctxt_to) const;
    void unPackOneOutput(const Ciphertext &ctxt_from,
                         LWE::Ciphertext &ctxt_to) const;

    void conversionToReal(const Plaintext &ptxt, Plaintext &ptxt_out) const;
    template <EncryptionType enc_type>
    void conversionToReal(const CiphertextBase<enc_type> &ctxt,
                          CiphertextBase<enc_type> &ctxt_out) const;
    void conversionToComplex(const Plaintext &ptxt, Plaintext &ptxt_out) const;
    void conversionToComplex(const Ciphertext &ctxt,
                             Ciphertext &ctxt_out) const;

    void switchModulus(const Ciphertext &ctxt, Ciphertext &ctxt_out,
                       u64 target_level) const;
};

} // namespace HEaaN
