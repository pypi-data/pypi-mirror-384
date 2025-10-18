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

#include "EVI/Enums.hpp"
#include "EVI/impl/Basic.cuh"
#include "EVI/impl/CKKSTypes.hpp"
#include "EVI/impl/ContextImpl.hpp"
#include "EVI/impl/KeyPackImpl.hpp"
#include "EVI/impl/SecretKeyImpl.hpp"
#include "EVI/impl/Type.hpp"
#include "utils/Exceptions.hpp"
#include "utils/Sampler.hpp"
#include "utils/span.hpp"

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#ifdef BUILD_WITH_HEM
#include "HEaaN/Encryptor.hpp"
#include "hem/Converter.hpp"
#include "hem/ModulusMatrix.hpp"
#include "hem/RawArray.hpp"
#endif
// deb header
#include <Context.hpp>
#include <Encryptor.hpp>
#include <InternalType.hpp>

namespace evi {
namespace detail {
class EncryptorInterface {
public:
    virtual ~EncryptorInterface() = default;
    virtual void loadEncKey(const std::string &dir_path) = 0;
    virtual void loadEncKey(std::istream &in) = 0;

    virtual Query encrypt(const span<float> msg, const EncodeType type = EncodeType::ITEM, const bool level = false,
                          std::optional<float> scale = std::nullopt) = 0;

    virtual Query encrypt(const span<float> msg, const SecretKey &seckey, const EncodeType type = EncodeType::ITEM,
                          const bool level = false, std::optional<float> scale = std::nullopt) = 0;

    virtual Query encrypt(const span<float> msg, const MultiSecretKey &seckey, const EncodeType type, const bool level,
                          std::optional<float> scale) = 0;

    virtual Query encrypt(const span<float> msg, const std::string &enckey_path,
                          const EncodeType type = EncodeType::ITEM, const bool level = false,
                          std::optional<float> scale = std::nullopt) = 0;

    virtual Query encrypt(const span<float> msg, const KeyPack &keypack, const EncodeType type = EncodeType::ITEM,
                          const bool level = false, std::optional<float> scale = std::nullopt) = 0;

    virtual std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg,
                                       const EncodeType type = EncodeType::ITEM, const bool level = false,
                                       std::optional<float> scale = std::nullopt) = 0;

    virtual std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const std::string &enckey_path,
                                       const EncodeType type = EncodeType::ITEM, const bool level = false,
                                       std::optional<float> scale = std::nullopt) = 0;

    virtual std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const KeyPack &keypack,
                                       const EncodeType type = EncodeType::ITEM, const bool level = false,
                                       std::optional<float> scale = std::nullopt) = 0;

    virtual Query encode(const span<float> msg, const EncodeType type = EncodeType::ITEM, const bool level = false,
                         std::optional<float> scale = std::nullopt) = 0;

    virtual Query encode(const std::vector<std::vector<float>> &msg, const EncodeType type = EncodeType::QUERY,
                         const int level = 0, std::optional<float> scale = std::nullopt) = 0;

#ifdef BUILD_WITH_HEM

    virtual std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const HEaaN::KeyPack he_keypack,
                                       const EncodeType type, const int level, std::optional<float> scale) = 0;

#endif

    virtual Blob encrypt(const span<float> msg, const int num_items, const bool level = false,
                         std::optional<float> scale = std::nullopt) = 0;
    virtual Blob encode(const span<float> msg, const int num_items, const bool level = false,
                        std::optional<float> scale = std::nullopt) = 0;

    virtual EvalMode getEvalMode() const = 0;
    virtual const Context &getContext() const = 0;
};

class RandomSampler;

template <EvalMode M>
class EncryptorImpl : public EncryptorInterface {
public:
    explicit EncryptorImpl(const Context &context, std::optional<std::vector<u8>> seed = std::nullopt);
    explicit EncryptorImpl(const Context &context, const KeyPack &keypack,
                           std::optional<std::vector<u8>> seed = std::nullopt);
    explicit EncryptorImpl(const Context &context, const std::string &path,
                           std::optional<std::vector<u8>> seed = std::nullopt);
    explicit EncryptorImpl(const Context &context, std::istream &in,
                           std::optional<std::vector<u8>> seed = std::nullopt);

    void loadEncKey(const std::string &dir_path) override;
    void loadEncKey(std::istream &in) override;
    void loadEncKey(const KeyPack &keypack);

    Query encrypt(const span<float> msg, const SecretKey &seckey, const EncodeType type = EncodeType::ITEM,
                  const bool level = false, std::optional<float> scale = std::nullopt) override;
    Query encrypt(const span<float> msg, const MultiSecretKey &seckey, const EncodeType type, const bool level,
                  std::optional<float> scale);
    Query encrypt(const span<float> msg, const EncodeType type = EncodeType::ITEM, const bool level = false,
                  std::optional<float> scale = std::nullopt) override;
    Query encrypt(const span<float> msg, const std::string &enckey_path, const EncodeType type, const bool level,
                  std::optional<float> scale) override;
    Query encrypt(const span<float> msg, const KeyPack &keypack, const EncodeType type, const bool level,
                  std::optional<float> scale) override;

    // test feature batch encrypt
    std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const EncodeType type = EncodeType::ITEM,
                               const bool level = false, std::optional<float> scale = std::nullopt) override;

    std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const std::string &enckey_path,
                               const EncodeType type = EncodeType::ITEM, const bool level = false,
                               std::optional<float> scale = std::nullopt) override;

    std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const KeyPack &keypack,
                               const EncodeType type = EncodeType::ITEM, const bool level = false,
                               std::optional<float> scale = std::nullopt) override;

    Query encode(const span<float> msg, const EncodeType type, const bool level = false,
                 std::optional<float> scale = std::nullopt) override;

    Query encode(const std::vector<std::vector<float>> &msg, const EncodeType type, const int level,
                 std::optional<float> scale) override;

    EvalMode getEvalMode() const override {
        return context_->getEvalMode();
    }
    const Context &getContext() const override {
        return context_;
    }

#ifdef BUILD_WITH_HEM

    std::vector<Query> encrypt(const std::vector<std::vector<float>> &msg, const HEaaN::KeyPack he_keypack,
                               const EncodeType type, const int level, std::optional<float> scale) override;

#endif

    Blob encrypt(const span<float> msg, const int num_items, const bool level = false,
                 std::optional<float> scale = std::nullopt) override;
    Blob encode(const span<float> msg, const int num_items, const bool level = false,
                std::optional<float> scale = std::nullopt) override;
    // std::vector<polyvec128> plainQueryForLv0HERS(const span<float> msg, std::optional<float> scale =
    // std::nullopt);

    // std::vector<u64> packingWithModPackKey(KeyPack keys,
    //                                        std::vector<std::shared_ptr<evi::SingleCiphertext>> ciphers);
private:
    Query::SingleQuery innerEncrypt(const span<float> &msg, const bool level, const double scale,
                                    std::optional<const SecretKey> seckey = std::nullopt,
                                    std::optional<bool> ntt = true);
    Query::SingleQuery innerEncode(const span<float> &msg, const bool level, const double scale,
                                   std::optional<const u64> msg_size = std::nullopt, std::optional<bool> ntt = true);

    const Context context_;
    RandomSampler sampler_;
    deb::Encryptor deb_encryptor_;
    FixedKeyType encKey_;
    deb::deb_swk deb_encKey_;

    VariadicKeyType switchKey_;
    bool enc_loaded_ = false;
};

class Encryptor : public std::shared_ptr<EncryptorInterface> {
public:
    Encryptor(std::shared_ptr<EncryptorInterface> impl) : std::shared_ptr<EncryptorInterface>(std::move(impl)) {}
};

Encryptor makeEncryptor(const Context &context, std::optional<std::vector<u8>> seed = std::nullopt);
Encryptor makeEncryptor(const Context &context, const KeyPack &keypack,
                        std::optional<std::vector<u8>> seed = std::nullopt);
Encryptor makeEncryptor(const Context &context, const std::string &path,
                        std::optional<std::vector<u8>> seed = std::nullopt);
Encryptor makeEncryptor(const Context &context, std::istream &in, std::optional<std::vector<u8>> seed = std::nullopt);
} // namespace detail
} // namespace evi
