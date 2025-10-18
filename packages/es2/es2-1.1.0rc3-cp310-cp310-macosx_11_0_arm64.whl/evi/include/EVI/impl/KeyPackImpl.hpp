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
#include "EVI/impl/Type.hpp"

#include "EVI/Enums.hpp"
#include "utils/Exceptions.hpp"
#include "utils/SealInfo.hpp"

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
// deb header
#include <InternalType.hpp>
#include <Serialize.hpp>

namespace evi {

namespace fs = std::filesystem;

namespace detail {

class IKeyPack {
public:
    virtual ~IKeyPack() = default;

    virtual void saveEncKeyFile(const std::string &path) const = 0;
    virtual void getEncKeyBuffer(std::ostream &os) const = 0;
    virtual void loadEncKeyFile(const std::string &path) = 0;
    virtual void loadEncKeyBuffer(std::istream &is) = 0;

    virtual void saveEvalKeyFile(const std::string &path) const = 0;
    virtual void getEvalKeyBuffer(std::ostream &os) const = 0;
    virtual void loadEvalKeyFile(const std::string &path) = 0;
    virtual void loadEvalKeyBuffer(std::istream &is) = 0;
};

class KeyPackData : public IKeyPack {
public:
    KeyPackData() = delete;
    KeyPackData(const evi::detail::Context &context);
    KeyPackData(const evi::detail::Context &context, std::istream &in);
    KeyPackData(const evi::detail::Context &context, std::string &dir_path);
    ~KeyPackData() = default;

    // override func
    void saveEncKeyFile(const std::string &path) const override;
    void getEncKeyBuffer(std::ostream &os) const override;
    void loadEncKeyFile(const std::string &path) override;
    void loadEncKeyBuffer(std::istream &is) override;

    void saveEvalKeyFile(const std::string &path) const override;
    void getEvalKeyBuffer(std::ostream &os) const override;
    void loadEvalKeyFile(const std::string &path) override;
    void loadEvalKeyBuffer(std::istream &is) override;

    void serialize(std::ostream &os) const;
    void deserialize(std::istream &is);

    void saveModPackKeyFile(const std::string &path) const;
    void getModPackKeyBuffer(std::ostream &os) const;
    void saveRelinKeyFile(const std::string &path) const;
    void getRelinKeyBuffer(std::ostream &os) const;

    void loadRelinKeyFile(const std::string &path);
    void loadRelinKeyBuffer(std::istream &is);
    void loadModPackKeyFile(const std::string &path);
    void loadModPackKeyBuffer(std::istream &is);

    void save(const std::string &path);

    FixedKeyType encKey;
    FixedKeyType relinKey;
    deb::deb_swk deb_encKey;
    deb::deb_swk deb_relinKey;

    VariadicKeyType modPackKey;
    VariadicKeyType sharedAModPackKey;
    VariadicKeyType CCSharedAModPackKey;
    VariadicKeyType switchKey;
    VariadicKeyType sharedAKey;
    VariadicKeyType reverseSwitchKey;
    std::vector<VariadicKeyType> additiveSharedAKey;
    deb::deb_swk deb_modPackKey;

    int num_shared_secret;

    bool shared_a_key_loaded_;
    bool shared_a_mod_pack_loaded_;
    bool cc_shared_a_mod_pack_loaded_;
    bool enc_loaded_;
    bool eval_loaded_;

    const evi::detail::Context context_;
};

#ifdef BUILD_WITH_HEM
class HEaaNKeyPack : public IKeyPack {
public:
    HEaaNKeyPack(const evi::detail::Context &context);

    void saveEncKeyFile(const std::string &dir_path) const override {
        he_keypack_.save(dir_path);
    };
    void getEncKeyBuffer(std::ostream &os) const override {
        he_keypack_.save(os);
    };
    void loadEncKeyFile(const std::string &file_path) override {
        std::ifstream in(file_path, std::ios::binary);
        if (!in) {
            throw std::runtime_error("Cannot open file: " + file_path);
        }
        he_keypack_.loadEncKey(in);
    };
    void loadEncKeyBuffer(std::istream &stream) override {
        he_keypack_.loadEncKey(stream);
    };

    void saveEvalKeyFile(const std::string &dir_path) const override {
        throw std::logic_error("HEaaNKeyPack::saveEvalKey not implemented yet");
    };
    void getEvalKeyBuffer(std::ostream &os) const override {
        throw std::logic_error("HEaaNKeyPack::saveEvalKey not implemented yet");
    };
    void loadEvalKeyFile(const std::string &file_path) override {
        throw std::logic_error("HEaaNKeyPack::loadEvalKey not implemented yet");
    };
    void loadEvalKeyBuffer(std::istream &stream) override {
        throw std::logic_error("HEaaNKeyPack::loadEvalKey not implemented yet");
    };

#ifdef BUILD_WITH_HEM
    HEaaN::KeyPack genHEaaNEncKey(HEaaN::SecretKey he_seckey);

    HEaaN::KeyPack &getHEaaNKeyPack() {
        return he_keypack_;
    }
#endif

private:
    HEaaN::Context he_context_ = HEaaN::makeContext(HEaaN::ParameterPreset::FGbD12L0);
    HEaaN::KeyPack he_keypack_;
    const evi::detail::Context context_;
    bool enc_loaded_;
    bool eval_loaded_;
};

#endif

using KeyPack = std::shared_ptr<IKeyPack>;

KeyPack makeKeyPack(const evi::detail::Context &context);
KeyPack makeKeyPack(const evi::detail::Context &context, std::istream &in);
KeyPack makeKeyPack(const evi::detail::Context &context, std::string &dir_path);

} // namespace detail
} // namespace evi
