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
#include "EVI/Export.hpp"
#include <istream>
#include <memory>
#include <optional>
#include <ostream>

namespace evi {

namespace detail {
class SearchResult;
}

/**
 * @class SearchResult
 * @brief Represents the encrypted result of a search operation.
 *
 * A `SearchResult` holds the encrypted data returned from a homomorphic
 * search. To interpret the result, it must be decrypted
 * using a `Decryptor` and a valid `SecretKey`.
 */
class EVI_API SearchResult {
public:
    /// @brief Default constructor creates an empty `SearchResult`.
    SearchResult() = default;

    /**
     * @brief Constructs a `SearchResult` from an internal implementation.
     * @param impl Shared pointer to the internal `detail::SearchResult` object.
     */
    explicit SearchResult(std::shared_ptr<detail::SearchResult> impl);

    /**
     * @brief Deserializes a `SearchResult` from an input stream.
     * @param is Input stream containing the serialized search result.
     * @return A deserialized `SearchResult` instance.
     */
    static SearchResult deserializeFrom(std::istream &is);

    /**
     * @brief Serializes a `SearchResult` to an output stream.
     * @param res The `SearchResult` instance to serialize.
     * @param os Output stream to write the serialized result.
     */
    static void serializeTo(const SearchResult &res, std::ostream &os);

    /**
     * @brief Returns the number of items currently stored.
     * @return Item count.
     */
    uint32_t getItemCount();

private:
    std::shared_ptr<detail::SearchResult> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::SearchResult> &getImpl(SearchResult &) noexcept;
    friend const std::shared_ptr<detail::SearchResult> &getImpl(const SearchResult &) noexcept;
    /// @endcond
};

} // namespace evi
