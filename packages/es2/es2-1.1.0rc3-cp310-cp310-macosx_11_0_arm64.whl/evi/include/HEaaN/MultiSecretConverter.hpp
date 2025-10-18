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
#include "HEaaN/IncreaseNSKeyBundle.hpp"
#include "HEaaN/LWE/Ciphertext.hpp"
#include "HEaaN/MStoSSKeyBundle.hpp"
#include "HEaaN/RingSwitchKey.hpp"
#include "HEaaN/SStoMSBisectionKeyBundle.hpp"
#include "HEaaN/SStoMSKeyBundle.hpp"

#include <vector>

namespace HEaaN {

class HEAAN_API MultiSecretConverter {
public:
    void MStoSS(const MSRLWECiphertext &ctxt_from, // NOLINT
                const MStoSSKeyBundle &mstoss_key_bundle,
                const Context &context_to,
                std::vector<Ciphertext> &ctxt_to) const;

    void SStoMS(const std::vector<Ciphertext> &ctxt_from, // NOLINT
                const SStoMSKeyBundle &sstoms_key_bundle,
                MSRLWECiphertext &ctxt_to) const;

    void IncreaseNS(const std::vector<MSRLWECiphertext> &ctxt_from, // NOLINT
                    const IncreaseNSKeyBundle &increase_ns_key_bundle,
                    MSRLWECiphertext &ctxt_to) const;

    void
    SStoMSBisection(const std::vector<Ciphertext> &ctxt_from, // NOLINT
                    const SStoMSBisectionKeyBundle &sstoms_bisection_key_bundle,
                    MSRLWECiphertext &ctxt_to) const;
};

} // namespace HEaaN
