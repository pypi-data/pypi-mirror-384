////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2024, CryptoLab Inc. All rights reserved.               //
//                                                                            //
// This software and/or source code may be commercially used and/or           //
// disseminated only with the written permission of CryptoLab Inc,            //
// or in accordance with the terms and conditions stipulated in the           //
// agreement/contract under which the software and/or source code has been    //
// supplied by CryptoLab Inc. Any unauthorized commercial use and/or          //
// dissemination of this file is strictly prohibited and will constitute      //
// an infringement of copyright.                                              //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "EVI/impl/Basic.cuh"
#include "EVI/impl/CKKSTypes.hpp"
#include "EVI/impl/Const.hpp"
#include "EVI/impl/ContextImpl.hpp"
#include "EVI/impl/NTT.hpp"
#include "EVI/impl/Type.hpp"
#include "utils/SealInfo.hpp"
#include "utils/crypto/TEEWrapper.hpp"

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#ifdef BUILD_WITH_HEM
#include "HEaaN/Context.hpp"
#include "HEaaN/KeyGenerator.hpp"
#include "HEaaN/KeyPack.hpp"
#include "HEaaN/SecretKey.hpp"
#endif

#include <InternalType.hpp>
#include <Serialize.hpp>

namespace evi {

namespace fs = std::filesystem;

namespace detail {
struct SecretKeyData {
    SecretKeyData(const evi::detail::Context &context);
    SecretKeyData(const std::string &path, std::optional<SealInfo> sInfo = std::nullopt);

    void loadSecKey(const std::string &dir_path);
    void saveSecKey(const std::string &dir_path) const;

    void loadSealedSecKey(const std::string &dir_path);
    void saveSealedSecKey(const std::string &dir_path);

    void serialize(std::ostream &os) const;
    void deserialize(std::istream &is);

    s_poly &getCoeff() {
        return sec_coeff_;
    }
    poly &getKeyQ() {
        return sec_key_q_;
    }
    poly &getKeyP() {
        return sec_key_p_;
    }

    evi::ParameterPreset preset_;
    deb::deb_sk deb_sk_;

    s_poly sec_coeff_;
    poly sec_key_q_;
    poly sec_key_p_;

    bool sec_loaded_;

    std::optional<SealInfo> sInfo_;
    std::optional<TEEWrapper> teew_;
};

class SecretKey : public std::shared_ptr<SecretKeyData> {
public:
    SecretKey() : std::shared_ptr<SecretKeyData>(NULL) {}
    SecretKey(std::shared_ptr<SecretKeyData> data) : std::shared_ptr<SecretKeyData>(data) {}
};

SecretKey makeSecKey(const evi::detail::Context &context);
SecretKey makeSecKey(const std::string &path, std::optional<SealInfo> sInfo = std::nullopt);

using MultiSecretKey = std::vector<std::shared_ptr<SecretKeyData>>;

} // namespace detail
} // namespace evi
