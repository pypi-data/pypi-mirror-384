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

#include "EVI/ComputeBuffer.hpp"
#include "EVI/Export.hpp"
#include "EVI/Index.hpp"
#include "EVI/KeyPack.hpp"
#include "EVI/SearchResult.hpp"
#include <memory>
#include <optional>

#ifdef BUILD_WITH_HEM
#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Message.hpp"
#endif

namespace evi {

namespace detail {
class HomEvaluator;
}

/**
 * @class HomEvaluator
 * @brief Performs homomorphic search operations on encrypted data.
 *
 * The `HomEvaluator` uses evaluation keys to enable encrypted search over
 * an `Index`. It takes an encrypted query and returns encrypted search
 * results that can later be decrypted.
 */
class EVI_API HomEvaluator {
public:
    /// @brief Empty handle; initialize with makeHomEvaluator() before use.
    HomEvaluator() : impl_(nullptr) {}

    /**
     * @brief Constructs a HomEvaluator with an internal implementation.
     * @param impl Shared pointer to the internal `detail::HomEvaluator` object.
     */
    explicit HomEvaluator(std::shared_ptr<detail::HomEvaluator> impl) noexcept;

    /**
     * @brief Loads evaluation keys required for homomorphic search.
     * @param keypack `KeyPack` containing the evaluation keys.
     */
    void loadEvalKey(const evi::KeyPack &keypack);

    /**
     * @brief Loads evaluation keys required for homomorphic search.
     * @param file_path Path to the evaluation key file.
     */
    void loadEvalKey(const std::string &file_path);

    /**
     * @brief Loads evaluation keys required for homomorphic search.
     * @param stream Input stream containing the evaluation keys.
     */
    void loadEvalKey(std::istream &stream);

    /**
     * @brief Performs an encrypted search over the given index.
     * @param db Encrypted index containing stored items.
     * @param query Encrypted query used for search.
     * @param buf Compute buffer used for intermediate computations.
     * @return Encrypted search results as `SearchResult`.
     */
    evi::SearchResult search(const evi::Index &db, const evi::Query &query,
                             std::optional<ComputeBuffer> buf = std::nullopt);

private:
    std::shared_ptr<detail::HomEvaluator> impl_;
};

/**
 * @brief Creates a `HomEvaluator` instance for homomorphic search.
 *
 * @param context Context used for key initialization and device selection.
 * @return Configured `HomEvaluator` instance.
 */
EVI_API HomEvaluator makeHomEvaluator(const Context &context);

} // namespace evi
