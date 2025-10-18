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
// #include "EVI/Parameter.hpp"
#include <memory>
#include <optional>
#include <vector>

namespace evi {
namespace detail {
class Context;
}

/**
 * @class Context
 * @brief Represents the runtime context for homomorphic encryption operations.
 *
 * This class holds internal-related configuration and resources, such as device selection,
 * dimension, and parameter presets.
 *
 * To construct a Context instance, use the `makeContext` or `makeMultiContext` factory functions.
 */
class EVI_API Context {
public:
    /// @brief Empty handle; initialize with makeContext() or makeMultiContext() before use.
    Context() : impl_(nullptr) {}

    /**
     * @brief Constructs a Context from an internal implementation.
     * @param impl Shared pointer to the internal `detail::Context` object.
     */
    explicit Context(std::shared_ptr<detail::Context> impl) noexcept;

    /**
     * @brief Returns the device type (CPU/GPU) backing this Context.
     * @return The configured device type.
     */
    DeviceType getDeviceType();

    /**
     * @brief Returns the scaling factor used for encoding.
     * @return Scaling factor as a double.
     */
    double getScaleFactor() const;

    /**
     * @brief Returns the internal padded rank used.
     * @return The padded rank size.
     */
    double getPadRank() const;

    /**
     * @brief Returns the show rank, user-specified input vector length, for this Context.
     * @return The show rank size.
     */
    uint32_t getShowDim() const;

    /**
     * @brief Get the evaluation mode used in this context. (e.g FLAT, RMP, MM)
     * @return EvalMode The evaluation mode.
     */
    EvalMode getEvalMode() const;

private:
    std::shared_ptr<detail::Context> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::Context> &getImpl(Context &) noexcept;
    friend const std::shared_ptr<detail::Context> &getImpl(const Context &) noexcept;
    /// @endcond
};

/**
 * @brief Creates a new Context instance with the given encryption parameters.
 *
 * @param preset Parameter preset for homomorphic encryption (e.g., IP0).
 * @param deviceType Target device type (CPU or GPU).
 * @param dim Dimension of input vectors.
 * @param evalMode Evaluation mode to use (RMP, FLAT).
 * @param deviceId Optional device ID for GPU execution.
 * @return A configured `Context` object.
 */
EVI_API Context makeContext(evi::ParameterPreset preset, const evi::DeviceType deviceType, const uint64_t dim,
                            const evi::EvalMode evalMode, std::optional<const int> deviceId = std::nullopt);

/**
 * @brief Creates multiple Context instances for use with multiple dimensions.
 *
 * @param preset Parameter preset for homomorphic encryption (e.g., IP0).
 * @param deviceType Target device type (CPU or GPU).
 * @param evalMode Evaluation mode to use (RMP, FLAT).
 * @param deviceId Optional device ID for GPU execution.
 * @return A list of configured `Context` objects.
 */
EVI_API std::vector<Context> makeMultiContext(evi::ParameterPreset preset, evi::DeviceType deviceType,
                                              evi::EvalMode evalMode, std::optional<const int> deviceId = std::nullopt);

} // namespace evi
