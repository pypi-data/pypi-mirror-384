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
#include "EVI/impl/SecretKeyImpl.hpp"
#include "EVI/impl/Type.hpp"
#include "utils/Exceptions.hpp"
#include "utils/span.hpp"

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#ifdef BUILD_WITH_HEAAN
#include "Cleaner/Cleaner.hpp"
#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Decryptor.hpp"
#include "HEaaN/Message.hpp"
#include "HEaaN/ParameterPreset.hpp"
#endif

#ifdef BUILD_WITH_HEM
#include "HEaaN/Decryptor.hpp"
#include "hem/Converter.hpp"
#include "hem/ModulusMatrix.hpp"
#include "hem/RawArray.hpp"
#endif
// deb header
#include <Decryptor.hpp>

namespace evi {

namespace detail {

class DecryptorImpl {
public:
    explicit DecryptorImpl(const Context &context);

    Message decrypt(const SearchResult ctxt, const SecretKey &key, bool is_score,
                    std::optional<double> scale = std::nullopt);

    Message decrypt(const SearchResult ctxt, const std::string &key_path, bool is_score,
                    std::optional<double> scale = std::nullopt);

    Message decrypt(const Query ctxt, const SecretKey &key, std::optional<double> scale = std::nullopt);

    Message decrypt(const Query ctxt, const std::string &key_path, std::optional<double> scale = std::nullopt);

    Message decrypt(const int idx, const Query ctxt, const SecretKey &key, std::optional<double> scale = std::nullopt);

#ifdef BUILD_WITH_HEM

    Message decryptMatrix(const SearchResult ctxts, const std::string seckey_path, bool is_score = true,
                          std::optional<double> scale = std::nullopt);

    Message decryptMatrix(const SearchResult ctxts, const SecretKey &key, bool is_score = true,
                          std::optional<double> scale = std::nullopt);

    Message decryptMatrix(const Query ctxts, const std::string seckey_path, std::optional<double> scale = std::nullopt);

    Message decryptMatrix(const Query ctxts, const SecretKey &key, std::optional<double> scale = std::nullopt);

#endif
#ifdef BUILD_WITH_HEAAN

    explicit DecryptorImpl(const std::string &path);
    void decrypt(const HEaaN::Ciphertext &ctxt, HEaaN::Message &dmsg);

    std::optional<HEaaN::Context> heaan_context_;
    std::shared_ptr<HEaaN::Decryptor> heaan_dec_;
    std::shared_ptr<HEaaN::SecretKey> heaan_sk_;
    std::shared_ptr<HEaaN::Cleaner> heaan_cleaner_;

    std::shared_ptr<HEaaN::Cleaner> getCleaner() {
        return heaan_cleaner_;
    }

    HEaaN::Context &getHEaaNContext() {
        return heaan_context_.value();
    }

#else
private:
    deb::Decryptor deb_dec_;
#endif
private:
    const Context context_;
};

class Decryptor : public std::shared_ptr<DecryptorImpl> {
public:
    Decryptor(std::shared_ptr<DecryptorImpl> impl) : std::shared_ptr<DecryptorImpl>(impl) {}
};

Decryptor makeDecryptor(const Context &context);

#ifdef BUILD_WITH_HEAAN
Decryptor makeDecryptor(const std::string &path);
#endif

} // namespace detail
} // namespace evi
