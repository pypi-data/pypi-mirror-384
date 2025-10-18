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
#include "EVI/Context.hpp"
#include "EVI/Export.hpp"
#include "EVI/SealInfo.hpp"
#include <memory>
#include <optional>
#include <vector>

namespace evi {
namespace detail {
class SecretKey;
}

/**
 * @class SecretKey
 * @brief Represents a secret key used for homomorphic encryption.
 *
 * A `SecretKey` is required to derive public keys (e.g., encryption/evaluation keys)
 * and to perform encryption/decryption.
 */
class EVI_API SecretKey {
public:
    /// @brief Empty handle; initialize with makeSecKey() before use.
    SecretKey() : impl_(nullptr) {}

    /**
     * @brief Constructs a SecretKey from an internal implementation.
     * @param impl Shared pointer to the internal `detail::SecretKey` object.
     */
    SecretKey(std::shared_ptr<detail::SecretKey> impl) : impl_(std::move(impl)) {}

private:
    std::shared_ptr<detail::SecretKey> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::SecretKey> &getImpl(SecretKey &) noexcept;
    friend const std::shared_ptr<detail::SecretKey> &getImpl(const SecretKey &) noexcept;
    /// @endcond
};

/**
 * @brief Creates a empty SecretKey associated with the given context.
 *
 * @param context Context used for key initialization and device selection.
 * @return A new `SecretKey` instance.
 */
EVI_API SecretKey makeSecKey(const evi::Context &context);

/**
 * @brief Load the secret key from a file.
 * @param file_path Path to the secret key file.
 * @param sInfo  Optional sealing information for unsealing the secret key.
 * @return A new `SecretKey` instance.
 */
EVI_API SecretKey makeSecKey(const std::string &file_path, std::optional<SealInfo> sInfo = std::nullopt);

/// @brief Alias representing multiple secret keys.
using MultiSecretKey = std::vector<SecretKey>;

} // namespace evi
