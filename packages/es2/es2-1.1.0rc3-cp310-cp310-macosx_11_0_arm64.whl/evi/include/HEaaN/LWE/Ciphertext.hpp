////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2023 Crypto Lab Inc.                                    //
//                                                                            //
// - This file is part of HEaaN homomorphic encryption library.               //
// - HEaaN cannot be copied and/or distributed without the express permission //
//  of Crypto Lab Inc.                                                        //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "HEaaN/LWE/Context.hpp"
#include "HEaaN/Pointer.hpp"
#include "HEaaN/device/Device.hpp"

namespace HEaaN {
class LevelledElement;
class LevelledVector;

namespace LWE {
class CiphertextImpl;

///
/// @brief A class of LWE ciphertexts each of which contains a levelled vector
/// and a levelled element.
///
class HEAAN_API Ciphertext {
public:
    explicit Ciphertext(const Context &context);

    /// @brief Get the A part of ciphertext
    LevelledVector &getAx();
    /// @brief Get the B part of ciphertext
    LevelledElement &getBx();
    /// @brief Get const A part of ciphertext
    const LevelledVector &getAx() const;
    /// @brief Get const B part of ciphertext
    const LevelledElement &getBx() const;

    /// @brief Get the @p level -th data of A part
    u64 *getAxData(u64 level) const;
    /// @brief Get the B part data
    u64 *getBxData() const;

    /// @brief Save a ciphertext to a file
    void save(const std::string &path) const;
    /// @brief Save a ciphertext to stream
    void save(std::ostream &stream) const;

    /// @brief Load a ciphertext from a file
    void load(const std::string &path);
    /// @brief Load a ciphertext from stream
    void load(std::istream &stream);

    /// @brief Rescaling flag
    /// @returns The amount of extra deltas multiplied
    int getRescaleCounter() const;
    /// @brief Set rescale counter
    void setRescaleCounter(int r_counter);

    /// @brief Get level of a ciphertext
    /// @returns The current level of the ciphertext
    u64 getLevel() const;
    /// @brief Set level of a ciphertext
    /// @param[in] level
    void setLevel(u64 level);

    /// @brief Get device in which a ciphertext resides
    const Device &getDevice() const;

    /// @brief Send a ciphertext to given device
    /// @param[in] device
    void to(const Device &device);

    /// @brief Allocate memory for a ciphertext at given device
    /// @param[in] device
    void allocate(const Device &device);

    ///@brief Get Context context
    const Context &getContext() const;

private:
    Pointer<CiphertextImpl> impl_;
};
} // namespace LWE
} // namespace HEaaN
