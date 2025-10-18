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
#include "HEaaN/Integers.hpp"
#include "HEaaN/LWE/Ciphertext.hpp"
#include "HEaaN/LWE/SecretKey.hpp"
#include "HEaaN/Real.hpp"

namespace HEaaN::LWE {

///
///@brief Abstract entity for encrypting messages into ciphertexts
///
class HEAAN_API Encryptor {
public:
    explicit Encryptor(const Context &context);

    ///@brief Encrypt a real number to LWE ciphertext, to the maximal
    /// supported level, to rescale counter zero.
    ///@param[in] msg_val
    ///@param[in] sk
    ///@param[out] ctxt
    void encrypt(const Real msg_val, const SecretKey &sk,
                 Ciphertext &ctxt) const;

    ///@brief Encrypt a real number to LWE ciphertext, to a certain level, to a
    /// certain rescale counter.
    ///@param[in] msg_val
    ///@param[in] sk
    ///@param[in] level
    ///@param[in] r_counter
    ///@param[out] ctxt
    void encrypt(const Real msg_val, const SecretKey &sk, Ciphertext &ctxt,
                 u64 level, int r_counter = 0) const;

private:
    const Context context_;
};

} // namespace HEaaN::LWE
