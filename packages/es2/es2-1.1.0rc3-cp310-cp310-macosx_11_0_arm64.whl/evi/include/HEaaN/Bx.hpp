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
#include "HEaaN/EncryptionType.hpp"
#include "HEaaN/HEaaNExport.hpp"
#include "HEaaN/Pointer.hpp"
#include "HEaaN/Real.hpp"
#include "HEaaN/device/Device.hpp"

namespace HEaaN {
class Polynomial;
class PolynomialVector;

///
///@brief A class of RLWE/MLWE ciphertexts each of which contains a vector of
/// polynomials of length > 1.
///
class HEAAN_API Bx {

public:
    explicit Bx(const Context &context, u64 size, bool is_extended = false);
    // prevents construction with a boolean as the second parameter.
    Bx(const Context &context, bool) = delete;

    PolynomialVector &getData();
    const PolynomialVector &getData() const;
    u64 getLevel();
    u64 getLevel() const;
    bool isModUp() const;
    const Context &getContext() const;
    void to(const Device &device);
    void allocate(const Device &device);

private:
    std::shared_ptr<PolynomialVector> data_;
};

} // namespace HEaaN
