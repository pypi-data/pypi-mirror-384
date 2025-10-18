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
#include <memory>

namespace evi {
namespace detail {
struct IQuery;
}

/**
 * @class SingleQuery
 * @brief Lightweight handle to a single encoded/encrypted block used in a Query.
 *
 * Provides accessors for per-block metadata needed during search and evaluation.
 */
class EVI_API SingleQuery {
public:
    /// @brief Default-constructs an empty handle.
    SingleQuery() noexcept = default;

    /**
     * @brief Constructs a SingleQuery from an internal implementation.
     * @param impl Shared pointer to the internal `detail::IQuery` object.
     */
    explicit SingleQuery(std::shared_ptr<detail::IQuery> impl) noexcept;

    /**
     * @brief Returns the number of items currently stored.
     * @return Item count.
     */
    uint32_t getItemCount() const noexcept;

private:
    std::shared_ptr<detail::IQuery> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::IQuery> &getImpl(SingleQuery &) noexcept;
    friend const std::shared_ptr<detail::IQuery> &getImpl(const SingleQuery &) noexcept;
    /// @endcond
};

} // namespace evi
