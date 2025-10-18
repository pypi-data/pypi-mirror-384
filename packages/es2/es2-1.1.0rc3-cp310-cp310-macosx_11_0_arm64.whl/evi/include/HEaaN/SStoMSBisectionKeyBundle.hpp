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
#include "HEaaN/SStoMSKeyBundle.hpp"
#include "device/Device.hpp"
#include <memory>
#include <optional>
#include <ostream>

namespace HEaaN {

class HEAAN_API SStoMSBisectionKeyBundle {

public:
    explicit SStoMSBisectionKeyBundle(
        const Context &context_ss, const std::vector<Context> &context_ms_vec);

    explicit SStoMSBisectionKeyBundle(const Context &context_ms);

    const SStoMSKeyBundle &getSStoMSKeyBundle() const;
    SStoMSKeyBundle &getSStoMSKeyBundle();

    const IncreaseNSKeyBundle &getIncreaseNSKeyBundle(const u64 idx) const;
    IncreaseNSKeyBundle &getIncreaseNSKeyBundle(const u64 idx);

    const std::vector<IncreaseNSKeyBundle> &getIncreaseNSKeyBundleVec() const;
    std::vector<IncreaseNSKeyBundle> &getIncreaseNSKeyBundleVec();

    const Context &getMSContext(const u64 i) const;
    const Context &getSSContext() const;

    template <class Archive> void serialize(Archive &ar);

    void save(std::ostream &stream) const;
    void load(std::istream &stream);
    void to(const Device &device);

private:
    Context context_ss_;
    std::vector<Context> context_ms_vec_;

    SStoMSKeyBundle sstoms_keys_;
    std::vector<IncreaseNSKeyBundle> increase_ns_keys_vec_;
};
} // namespace HEaaN
