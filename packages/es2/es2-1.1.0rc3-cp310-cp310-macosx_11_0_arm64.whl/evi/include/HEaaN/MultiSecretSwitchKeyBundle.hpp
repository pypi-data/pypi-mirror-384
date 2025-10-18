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

#include "HEaaN/IncreaseNSKeyBundle.hpp"
#include "HEaaN/MStoSSKeyBundle.hpp"
#include "HEaaN/SStoMSBisectionKeyBundle.hpp"
#include "device/Device.hpp"
#include <memory>
#include <optional>
#include <ostream>

namespace HEaaN {

class HEAAN_API MultiSecretSwitchKeyBundle {

public:
    explicit MultiSecretSwitchKeyBundle(const Context &context_ss,
                                        const Context &context_ms);

    explicit MultiSecretSwitchKeyBundle(const Context &context_ss,
                                        const Context &context_ms,
                                        const Context &context_real_ss,
                                        const Context &context_real_ms);

    const MStoSSKeyBundle &getMStoSSKeyBundle() const;
    MStoSSKeyBundle &getMStoSSKeyBundle();

    const MStoSSKeyBundle &getMStoSSKeyBundleComplex() const;
    MStoSSKeyBundle &getMStoSSKeyBundleComplex();

    const SStoMSBisectionKeyBundle &getSStoMSBisectionKeyBundle() const;
    SStoMSBisectionKeyBundle &getSStoMSBisectionKeyBundle();

    const Context &getMSContext() const;
    const Context &getSSContext() const;

    template <class Archive> void serialize(Archive &ar) {
        ar(mstoss_keys_, sstoms_bisection_keys_);
    }

    void save(std::ostream &stream) const;
    void load(std::istream &stream);

    void save(const std::string &dir_path) const;
    void load(const std::string &dir_path);

    void to(const Device &device);

private:
    Context context_ss_;
    Context context_ms_;
    std::optional<Context> context_real_ss_;
    std::optional<Context> context_real_ms_;
    MStoSSKeyBundle mstoss_keys_;
    // mstoss_keys_complex_ is only used in case of ...
    // ... real-C2S-first bts.
    // In such cases, mstoss_keys_ are over reals...
    // ... and we need mstoss_keys_ over complex-ckks.
    // SStoMSKeyBundle sstoms_keys_;
    SStoMSBisectionKeyBundle sstoms_bisection_keys_;
    std::optional<MStoSSKeyBundle> mstoss_keys_complex_;
};
} // namespace HEaaN
