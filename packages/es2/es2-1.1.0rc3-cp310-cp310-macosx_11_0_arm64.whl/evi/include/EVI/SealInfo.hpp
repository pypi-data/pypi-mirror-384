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
#include <vector>

namespace evi {

/// @brief AES-256 key size in bytes.
constexpr int AES256_KEY_SIZE = 32;

namespace detail {
class SealInfo;
}

/**
 * @class SealInfo
 * @brief Encapsulates sealing configuration used to protect secret keys in in homomorphic encryption schemes during
 * storage.
 *
 * The `SealInfo` class holds information related to how a secret key (e.g., `SecretKey`) should be sealed
 * before being saved externally. Supported sealing modes include no sealing and AES-256 key wrapping.
 */
class EVI_API SealInfo {
public:
    /**
     * @brief Constructs a `SealInfo` with the specified sealing mode.
     * @param m Sealing mode to be used (e.g., `SealMode::NONE`, `SealMode::AES_KEK`).
     */
    SealInfo(SealMode m);

    /**
     * @brief Constructs a `SealInfo` for AES-KEK sealing with a raw 256-bit key.
     * @param m Sealing mode (must be `SealMode::AES_KEK`).
     * @param aes_key A 32-byte AES key used for key wrapping.
     */
    SealInfo(SealMode m, std::vector<uint8_t> aes_key);

    /// @cond INTERNAL
    SealInfo(SealMode m, int cm, int id, const std::string &pw);
    /// @endcond

    /**
     * @brief Retrieves the current sealing mode.
     * @return The configured `SealMode` value.
     */
    SealMode getSealMode() const;

private:
    std::shared_ptr<detail::SealInfo> impl_;

    /// @cond INTERNAL
    friend std::shared_ptr<detail::SealInfo> &getImpl(SealInfo &) noexcept;
    friend const std::shared_ptr<detail::SealInfo> &getImpl(const SealInfo &) noexcept;
    /// @endcond
};

} // namespace evi
