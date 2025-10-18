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
#include <vector>

namespace HEaaN {

class EvaluationKey;

///
///@brief A class of a bundle of switching keys which are used in
/// RingPacker::modPack
///
class HEAAN_API MStoSSKeyBundle {
public:
    ///@brief Create a MStoSSKeyBundle object
    ///@param[in] context
    explicit MStoSSKeyBundle(const Context &context);

    ///@brief Get the single switching key at given index
    ///@param[in] idx
    std::shared_ptr<EvaluationKey> getMStoSSKey(const u64 idx) const;

    ///@brief Save the bundle of keys to stream
    ///@param[in] stream
    void save(std::ostream &stream) const;

    ///@brief Load the bundle of keys from stream
    ///@param[in] stream
    void load(std::istream &stream);

    ///@brief Send the bundle of keys to given device
    ///@param[in] device
    void to(const Device &device);

    ///@brief Get the number of keys in the bundle
    u64 getNumKeys() const;

    template <class Archive> void serialize(Archive &ar);

private:
    Context context_;
    std::vector<std::shared_ptr<EvaluationKey>> mstoss_keys_;
};

} // namespace HEaaN
