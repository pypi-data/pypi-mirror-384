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
#include "EVI/Export.hpp"
#include "EVI/SingleQuery.hpp"
#include <memory>
#include <vector>

#ifdef BUILD_WITH_HEM
#include "HEaaN/Ciphertext.hpp"
#include "hem/ModulusMatrix.hpp"
#endif

namespace evi {
namespace detail {
class Query;
}

/**
 * @class Query
 * @brief Represents an encoded query or encrypted data vector used in homomorphic encryption.
 *
 * The `Query` holds encoded data for either an encrypted item or a search query.
 * It is typically generated using an `Encryptor` when encoding or encrypting data, and is used
 * during search or evaluation operations.
 */
class EVI_API Query {
public:
    Query() noexcept : impl_(nullptr) {}

    /**
     * @brief Constructs a Query from an internal implementation.
     * @param impl Shared pointer to the internal `detail::Query` object.
     */
    explicit Query(std::shared_ptr<detail::Query> impl) noexcept;

    /**
     * @brief Returns the computation level of item.
     * @return Level indicator.
     */
    uint32_t getLevel() const;

    /**
     * @brief Returns the show rank, user-specified input vector length, for this Context.
     * @return The show rank size.
     */
    uint32_t getShowDim() const;

    /**
     * @brief Returns the innter single query item count.
     * @return The innter item count.
     */
    uint32_t getInnerItemCount() const;

    /**
     * @brief Returns the number of blocks in this Query.
     * @return Number of blocks.
     */
    std::size_t size() const;

    /**
     * @brief Returns the number of items in the inner single query.
     * @return The inner item count.
     */
    static Query deserializeFrom(std::istream &is);

    /**
     * @brief Writes a Query to a binary stream.
     * @param query Query to serialize.
     * @param os Output stream to receive serialized data.
     */
    static void serializeTo(const Query &query, std::ostream &os);

    /**
     * @brief Writes Query blocks to a binary stream.
     * @param blocks Sequence of SingleQuery blocks to serialize.
     * @param os Output stream to receive serialized data.
     */
    static void serializeTo(const std::vector<evi::SingleQuery> &blocks, std::ostream &os);

    /**
     * @brief Writes multiple Query objects to a binary stream.
     * @param queries Sequence of queries to serialize.
     * @param os Output stream to receive serialized data.
     */
    static void serializeVectorTo(const std::vector<Query> &queries, std::ostream &os);

    /**
     * @brief Reads multiple Query objects from a binary stream.
     * @param is Input stream containing serialized queries.
     * @return Deserialized query sequence.
     */
    static std::vector<Query> deserializeVectorFrom(std::istream &is);

    /**
     * @brief Builds a Query from multiple blocks.
     * @param blocks Input blocks.
     * @return Aggregated Query.
     */
    static Query makeFromBlocks(const std::vector<evi::SingleQuery> &blocks);

    /**
     * @brief Returns the i-th block.
     * @param i index of the block to retrieve.
     * @return The requested block.
     */
    evi::SingleQuery getSingleQuery(std::size_t i) const;

#ifdef BUILD_WITH_HEM
    /**
     * @brief Returns the single matrix block contained in this Query.
     * @return Matrix block.
     */
    hem::CTMatrix<uint64_t> getMatrix() const;
#endif

private:
    std::shared_ptr<detail::Query> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::Query> &getImpl(Query &) noexcept;
    friend const std::shared_ptr<detail::Query> &getImpl(const Query &) noexcept;
    /// @endcond
};

} // namespace evi
