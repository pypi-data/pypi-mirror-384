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
#include "HEaaN/LWE/Ciphertext.hpp"
#include "HEaaN/LWE/SecretKey.hpp"
#include "HEaaN/Real.hpp"

namespace HEaaN::LWE {

///
///@brief Abstract entity for decrypting ciphertexts
///
class HEAAN_API Decryptor {
public:
    explicit Decryptor(const Context &context);
    ///@brief Decrypt an LWE ciphertext to a real number using a LWE secret key
    ///@param[in] ctxt
    ///@param[in] sk
    ///@param[out] msg_val
    void decrypt(const Ciphertext &ctxt, const SecretKey &sk,
                 Real &msg_val) const;

private:
    const Context context_;
};

} // namespace HEaaN::LWE
