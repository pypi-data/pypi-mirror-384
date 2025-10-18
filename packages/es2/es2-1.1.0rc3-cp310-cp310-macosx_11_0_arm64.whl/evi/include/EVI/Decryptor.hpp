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
#include "EVI/Message.hpp"
#include "EVI/Query.hpp"
#include "EVI/SearchResult.hpp"
#include "EVI/SecretKey.hpp"
#include <memory>

#ifdef BUILD_WITH_HEM
#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/SecretKey.hpp"
#include "hem/ModulusMatrix.hpp"
#endif

namespace evi {

namespace detail {
class Decryptor;
}

/**
 * @class Decryptor
 * @brief Decrypts queries and search results using a `SecretKey`.
 *
 * A `Decryptor` provides functions to convert encrypted data back into
 * plaintext `Message` objects. It supports decrypting individual queries,
 * ciphertexts, and search results.
 */
class EVI_API Decryptor {
public:
    /// @brief Empty handle; initialize with makeDecryptor() before use.
    Decryptor() : impl_(nullptr) {}

    /**
     * @brief Constructs a Decryptor with an internal implementation.
     * @param impl Shared pointer to the internal `detail::Decryptor` object.
     */
    explicit Decryptor(std::shared_ptr<detail::Decryptor> impl) noexcept;

    /**
     * @brief Decrypts a search result using the given secret key.
     * @param item Encrypted search result.
     * @param seckey Secret key used for decryption.
     * @return Decrypted `Message`.
     */
    Message decrypt(const SearchResult &item, const SecretKey &seckey);

    /**
     * @brief Decrypts a search result with optional score scaling.
     * @param item Encrypted search result.
     * @param seckey Secret key used for decryption.
     * @param is_score Indicates whether the decrypted result should be interpreted as a score.
     * @param scale Optional scaling factor for precise score computation.
     * @return Decrypted `Message`.
     */
    Message decrypt(const SearchResult &item, const SecretKey &seckey, bool is_score,
                    std::optional<double> scale = std::nullopt);

    /**
     * @brief Decrypts a search result using a key loaded from a file.
     * @param item Encrypted search result.
     * @param key_path Path to the secret key file.
     * @param is_score Indicates whether the decrypted result should be interpreted as a score.
     * @param scale Optional scaling factor for precise score computation.
     * @return Decrypted `Message`.
     */
    Message decrypt(const SearchResult &item, const std::string &key_path, bool is_score,
                    std::optional<double> scale = std::nullopt);

    /**
     * @brief Decrypts an entire encrypted query.
     * @param ctxt Encrypted query to decrypt.
     * @param key_path Path to the secret key file.
     * @param scale Optional scaling factor to adjust precision.
     * @return Decrypted `Message`.
     */
    Message decrypt(const Query &ctxt, const std::string &key_path, std::optional<double> scale = std::nullopt);

    /**
     * @brief Decrypts an entire encrypted query.
     * @param ctxt Encrypted query to decrypt.
     * @param seckey Secret key used for decryption.
     * @param scale Optional scaling factor to adjust precision.
     * @return Decrypted `Message`.
     */
    Message decrypt(const Query &ctxt, const SecretKey &seckey, std::optional<double> scale = std::nullopt);

    /**
     * @brief Decrypts a specific item from an encrypted query.
     * @param idx Index of the item to decrypt.
     * @param ctxt Encrypted query.
     * @param key Secret key used for decryption.
     * @param scale Optional scaling factor to adjust precision.
     * @return Decrypted `Message`.
     */
    Message decrypt(int idx, const Query &ctxt, const SecretKey &seckey, std::optional<double> scale = std::nullopt);

private:
    std::shared_ptr<detail::Decryptor> impl_;
};

/**
 * @brief Creates a `Decryptor` instance using the given context.
 *
 * @param context Context used for key initialization and device selection.
 * @return Configured `Decryptor` instance.
 */
EVI_API Decryptor makeDecryptor(const Context &context);

} // namespace evi
