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
#include "EVI/impl/ContextImpl.hpp"
#include "EVI/impl/KeyPackImpl.hpp"
#include "EVI/impl/NTT.hpp"
#include "EVI/impl/SecretKeyImpl.hpp"
#include "EVI/impl/Type.hpp"

#include "utils/Exceptions.hpp"
#include "utils/Sampler.hpp"

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#ifdef BUILD_WITH_HEAAN
#include "Cleaner/EvaluationResource.hpp"
#include "utils/Utils.hpp"
#endif
// deb header
#include <KeyGenerator.hpp>

namespace evi {
namespace detail {

class KeyGeneratorInterface {
public:
    virtual ~KeyGeneratorInterface() = default;
    virtual SecretKey genSecKey(std::optional<const int *> sec_coeff = std::nullopt) = 0;
    virtual void genEncKey(const SecretKey &seckey) = 0;
    virtual void genRelinKey(const SecretKey &seckey) = 0;
    virtual void genModPackKey(const SecretKey &seckey) = 0;
    virtual void genPubKeys(const SecretKey &seckey) = 0;
    virtual KeyPack &getKeyPack() = 0;

    virtual void genSharedASwitchKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) = 0;
    virtual void genAdditiveSharedASwitchKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) = 0;
    virtual void genSharedAModPackKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) = 0;
    virtual void genCCSharedAModPackKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) = 0;
    virtual std::vector<SecretKey> genMultiSecKey() = 0;
    virtual void genSwitchKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) = 0;
};

template <EvalMode M>
class KeyGeneratorImpl : public KeyGeneratorInterface {
public:
    KeyGeneratorImpl(const Context &context, KeyPack &pack, std::optional<std::vector<u8>> seed = std::nullopt);
    KeyGeneratorImpl(const Context &context, std::optional<std::vector<u8>> seed = std::nullopt);

    KeyGeneratorImpl() = delete;
    ~KeyGeneratorImpl() override = default;

    SecretKey genSecKey(std::optional<const int *> sec_coeff = std::nullopt) override;
    void genEncKey(const SecretKey &sec_key) override;
    void genRelinKey(const SecretKey &sec_key) override;
    void genModPackKey(const SecretKey &sec_key) override;
    void genPubKeys(const SecretKey &sec_key) override;

    void genSharedASwitchKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) override;
    void genAdditiveSharedASwitchKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) override;
    void genSharedAModPackKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) override;
    void genCCSharedAModPackKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) override;
    std::vector<SecretKey> genMultiSecKey() override;
    void genSwitchKey(const SecretKey &sec_from, const std::vector<SecretKey> &sec_to) override;

    KeyPack &getKeyPack() override {
        return pack_iface_;
    }

private:
    void genSecKeyFromCoeff(SecretKey &sec_key, const int *sec_coeff);
    void genSwitchingKey(const SecretKey &sec_key, span<u64> from_s, span<u64> out_a_q, span<u64> out_a_p,
                         span<u64> out_b_q, span<u64> out_b_p);
    const Context context_;
    deb::KeyGenerator deb_keygen_;

    KeyPack pack_iface_;
    std::shared_ptr<KeyPackData> pack_;
    std::shared_ptr<KeyPack> gen_pack_;

#ifdef BUILD_WITH_HEM
    std::shared_ptr<HEaaNKeyPack> he_pack_;
#endif

    RandomSampler sampler_;
};

class MultiKeyGenerator final {
public:
    MultiKeyGenerator(std::vector<Context> &context, const std::string &store_path, SealInfo &sInfo,
                      std::optional<std::vector<u8>> seed = std::nullopt);
    ~MultiKeyGenerator() = default;

    SecretKey generate_keys();
    SecretKey generate_sec_key();

    void generate_keys_from_sec_key(const std::string &sec_key_path);
    void generate_pub_key(SecretKey sec_key);
    void generate_eval_key();

    SecretKey save_evi_sec_key();

    KeyPack &get_key_pack() {
        return evi_keypack_[0];
    }

    bool checkFileExist();

private:
#ifdef BUILD_WITH_HEAAN
    HEaaN::Context heaan_context_hi_;
    HEaaN::Context heaan_context_;

    HEaaN::EvaluationResource heaan_eval_resource_;

    std::unique_ptr<HEaaN::SecretKey> heaan_sk_hi_;
    std::unique_ptr<HEaaN::SecretKey> heaan_sk_;

    HEaaN::Context heaan_context_clean_;

#endif

#ifdef BUILD_WITH_HEM
    void genHEaaNKey(SecretKey seckey);
#endif

    std::vector<Context> evi_context_;
    std::vector<KeyPack> evi_keypack_;

    std::shared_ptr<SealInfo> sInfo_;
    std::optional<TEEWrapper> teew_;

    std::shared_ptr<alea_state> as_;

    std::vector<int> rank_list_;
    std::vector<std::pair<int, int>> inner_rank_list_;
    evi::ParameterPreset preset_;
    std::filesystem::path store_path_;

    void initialize();

    bool save_all_keys(SecretKey sec_key);
    void save_enc_key();
    void save_eval_key();

    void save_evi_sec_key(SecretKey sec_key);

    bool save_sec_keys();
#ifdef BUILD_WITH_HEAAN
    bool save_sec_key16();
    bool save_sec_key12();
    bool save_sec_key16_sealed();
    bool save_sec_key12_sealed();
#endif

    void adjustRankList(std::vector<int> &rank_list);
};

class KeyGenerator : public std::shared_ptr<KeyGeneratorInterface> {
public:
    KeyGenerator(std::shared_ptr<KeyGeneratorInterface> ptr) : std::shared_ptr<KeyGeneratorInterface>(ptr) {}
    KeyGenerator &operator=(const std::shared_ptr<KeyGeneratorInterface> &other) {
        std::shared_ptr<KeyGeneratorInterface>::operator=(other);
        return *this;
    }
};

KeyGenerator makeKeyGenerator(const Context &context, KeyPack &pack,
                              std::optional<std::vector<u8>> seed = std::nullopt);
KeyGenerator makeKeyGenerator(const Context &context, std::optional<std::vector<u8>> seed = std::nullopt);

} // namespace detail
} // namespace evi
