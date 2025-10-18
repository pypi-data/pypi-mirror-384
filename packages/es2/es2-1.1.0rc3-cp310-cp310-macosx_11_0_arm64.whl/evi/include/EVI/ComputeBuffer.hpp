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
#include "EVI/KeyPack.hpp"
#include <memory>

namespace evi {

namespace detail {
class ComputeBuffer;
}

/**
 * @class ComputeBuffer
 * @brief Provides temporary storage for intermediate results during homomorphic operations.
 *
 * A `ComputeBuffer` is mainly used by `HomEvaluator` to manage memory and hold
 * intermediate data during encrypted search and evaluation.
 */
class EVI_API ComputeBuffer {
public:
    /// @brief Default constructor is deleted. Use `makeComputeBuffer()` factory function instead.
    ComputeBuffer() = delete;

    /**
     * @brief Constructs a `ComputeBuffer` from an internal implementation.
     * @param impl Shared pointer to the internal `detail::ComputeBuffer` object.
     */
    explicit ComputeBuffer(std::shared_ptr<detail::ComputeBuffer> impl) noexcept;

    /**
     * @brief Returns the execution Context associated with this buffer.
     * @return Context used for key initialization and device selection.
     */
    Context getContext() const;

private:
    std::shared_ptr<detail::ComputeBuffer> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::ComputeBuffer> &getImpl(ComputeBuffer &) noexcept;
    friend const std::shared_ptr<detail::ComputeBuffer> &getImpl(const ComputeBuffer &) noexcept;
    /// @endcond
};

/**
 * @brief Creates a `ComputeBuffer` configured for the given context.
 *
 * @param context Context used for key initialization and device selection.
 * @return A configured `ComputeBuffer` instance.
 */
EVI_API ComputeBuffer makeComputeBuffer(const Context &context);

} // namespace evi
