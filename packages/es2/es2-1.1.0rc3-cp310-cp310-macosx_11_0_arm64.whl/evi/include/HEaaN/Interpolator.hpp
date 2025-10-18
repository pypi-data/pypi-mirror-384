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

#include "Context.hpp"
#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/HEaaNExport.hpp"

namespace HEaaN {

class Device;
class HomEvaluator;
class InterpolatorImpl;

///
///@brief A class consisting of bootstrap and its related functions
///
class HEAAN_API Interpolator {
public:
    ///@brief Constructs a class for boostrap.
    /// Pre-computation of bootstrapping constants is included.
    ///@param[in] eval HomEvaluator to be used for bootstrapping.
    ///@param[in] log_slots
    ///@details Without `log_slots` argument,
    /// it pre-compute the boot constants for full slots
    explicit Interpolator(const HomEvaluator &eval);
    void removeI(const Ciphertext &ctxt, Ciphertext &ctxt_out,
                 Real cnst = 1.0) const;

    HomEvaluator &getEval() const;

private:
    std::shared_ptr<InterpolatorImpl> impl_;
    const std::shared_ptr<HomEvaluator> eval_;
};

} // namespace HEaaN
