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
#include "EVI/Query.hpp"

#ifdef BUILD_WITH_HEM
#include "hem/ModulusMatrix.hpp"
#endif

namespace evi {

namespace detail {
class Index;
}

/**
 * @class Index
 * @brief Manages an encrypted vector index for search and retrieval operations.
 *
 * The `Index` stores encrypted items as `Query` objects and provides
 * search functionality over the stored data. It supports appending
 * individual or multiple items and performing encrypted search queries.
 */
class EVI_API Index {
public:
    /// @brief Empty handle; initialize with makeIndex() before use.
    Index() noexcept : impl_(nullptr) {}

    /**
     * @brief Constructs an Index from an internal implementation.
     * @param impl Shared pointer to the internal `detail::Index` object.
     */
    explicit Index(std::shared_ptr<detail::Index> impl) noexcept;

    /**
     * @brief Appends a single encrypted item to the index.
     * @param item The encrypted `Query` representing an item to store.
     */
    void append(const Query &item);

    /**
     * @brief Appends multiple encrypted items to the index in batch.
     * @param items A vector of encrypted `Query` objects to store in the index.
     */
    void append(const std::vector<Query> &items);

    /**
     * @brief Appends multiple encrypted items to the index.
     * @param items A vector of encrypted `Query` objects.
     * @return A vector of IDs corresponding to the inserted items.
     */
    std::vector<uint64_t> batchAppend(const std::vector<Query> &items);

    /**
     * @brief Writes the index to a binary stream.
     * @param stream Output stream to receive serialized data.
     */
    void serializeTo(std::ostream &stream);

    /**
     * @brief Restores the index from a binary stream.
     * @param stream Input stream containing previously serialized data.
     */
    void deserializeFrom(std::istream &stream);

    /**
     * @brief Returns the show rank, user-specified input vector length, for this Context.
     * @return The show rank size.
     */
    uint32_t getShowDim();

    /**
     * @brief Returns the number of items currently stored.
     * @return Item count.
     */
    uint32_t getItemCount();

    /**
     * @brief Returns the computation level of items in the index.
     * @return Level indicator.
     */
    int getLevel();

private:
    std::shared_ptr<detail::Index> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::Index> &getImpl(Index &) noexcept;
    const friend std::shared_ptr<detail::Index> &getImpl(const Index &) noexcept;
    /// @endcond
};

/**
 * @brief Creates an `Index` instance using the given context and database type.
 *
 * @param context Context used for key initialization and device selection.
 * @param dbtype Type of data stored in the index (`CIPHER`, `PLAIN`).
 * @return A configured `Index` instance.
 */
EVI_API Index makeIndex(const Context &context, DataType dbtype);

} // namespace evi
