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

#include "HEaaN/Context.hpp"
#include "HEaaN/HEaaNExport.hpp"
#include "HEaaN/Integers.hpp"
#include "HEaaN/device/Device.hpp"

#include <memory>

namespace HEaaN {

class EvaluationKey;

///
///@brief A class of switching key which is used in
/// RingPacker::compose or RingPacker::decompose
///
class HEAAN_API RingSwitchKey : public std::shared_ptr<EvaluationKey> {
public:
    ///@brief Create a RingSwitchKey object
    ///@param[in] context
    explicit RingSwitchKey(const Context &context);

    ///@brief Save a key to stream
    ///@param[in] stream
    void save(std::ostream &stream) const;

    ///@brief Load a key from stream
    ///@param[in] stream
    void load(std::istream &stream);

    ///@brief Save a key to stream
    ///@param[in] stream
    void save(const std::string &dir_path) const;

    ///@brief Load a key from stream
    ///@param[in] stream
    void load(const std::string &dir_path);

    ///@brief Send a key to given device
    ///@param[in] device
    void to(const Device &device);

    ///@brief Get the PolyData of the Switching Key
    ///@param[in] index
    ///@param[in] device
    u64 *getAxPolyData(u64 index, u64 level, const Device &device);
    u64 *getBxPolyData(u64 index, u64 level, const Device &device);
};

} // namespace HEaaN
