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

#include "HEaaN/HEaaNExport.hpp"
#include "HEaaN/LWE/Ciphertext.hpp"
#include "HEaaN/Real.hpp"

namespace HEaaN::LWE {

class HomEvaluatorImpl;

///
///@brief A class consisting of basic operation of LWE Ciphertexts and Real
/// numbers
///
class HEAAN_API HomEvaluator {
public:
    explicit HomEvaluator(const Context &context);

    ///@brief Negate a LWECiphertext
    ///@param[in] ctxt
    ///@param[out] ctxt_out
    void negate(const Ciphertext &ctxt, Ciphertext &ctxt_out) const;

    ///@brief LWECiphertext + Real Constant
    ///@param[in] ctxt1
    ///@param[in] ctxt2
    ///@param[out] ctxt_out
    ///@details Add a real number to the message which LWECiphertext encrypts.
    void add(const Ciphertext &ctxt1, const Real &cnst_real,
             Ciphertext &ctxt_out) const;
    ///@brief LWECiphertext + LWECiphertext
    ///@param[in] ctxt1
    ///@param[in] ctxt2
    ///@param[out] ctxt_out
    ///@details Add two LWECiphertexts.
    void add(const Ciphertext &ctxt1, const Ciphertext &ctxt2,
             Ciphertext &ctxt_out) const;

    /// @brief LWECiphertext - Real Constant
    /// @param ctxt1
    /// @param cnst_real
    /// @param ctxt_out
    /// @details subtract a real number from the message which LWECiphertext
    /// encrypts.
    void sub(const Ciphertext &ctxt1, const Real &cnst_real,
             Ciphertext &ctxt_out) const;
    /// @brief LWECiphertext - LWECiphertext
    /// @param ctxt1
    /// @param ctxt2
    /// @param ctxt_out
    /// @details subtract two LWECiphertexts.
    void sub(const Ciphertext &ctxt1, const Ciphertext &ctxt2,
             Ciphertext &ctxt_out) const;

    /// @brief LWECiphertext * Real Constant
    /// @param ctxt1
    /// @param cnst_real
    /// @param ctxt_out
    /// @details multiply a real number from the message which LWECiphertext
    /// encrypts. Note that if the input `cnst_real` is
    /// sufficiently close to an integer, then the multiplication will take
    /// place via `multInteger`, i.e. without any depth consumption. More
    /// precisely, "sufficiently close" here means that the absolute value of
    /// the difference of its value with its closest
    /// integer is less than or equal to 1e-8.
    /// @throws  RuntimeException if ctxt1 has nonzero rescale counter.
    /// @throws RuntimeException if ctxt1 has no available level (level 0),
    /// unless `cnst_real` is sufficiently close to an integer
    void mult(const Ciphertext &ctxt1, const Real &cnst_real,
              Ciphertext &ctxt_out) const;

    /// @brief LWECiphertext * Integer
    /// @param ctxt
    /// @param cnst_integer
    /// @param ctxt_out
    ///@details multiply a LWECiphertext by a integer constant
    void multInteger(const Ciphertext &ctxt, i64 cnst_integer,
                     Ciphertext &ctxt_out) const;

    /// @brief Multiply LWECiphertext by a real constant
    /// @param ctxt1
    /// @param cnst_real
    /// @param ctxt_out
    void multWithoutRescale(const Ciphertext &ctxt1, const Real &cnst_real,
                            Ciphertext &ctxt_out) const;

    /// @brief Divide a LWECiphertext by the scale factor
    /// @param ctxt
    ///@details It transforms a lwe-ciphertext of a level ℓ encrypting a message
    /// m
    /// into a lwe-ciphertext of level ℓ-1 encrypting the message {q_ℓ}^{-1} m.
    ///@throws RuntimeException if ctxt has nonzero rescale counter.
    void rescale(Ciphertext &ctxt) const;

    /// @brief Decrease the level of LWECiphertext
    /// @param ctxt
    /// @param target_level
    /// @param ctxt_out
    void levelDown(const Ciphertext &ctxt, u64 target_level,
                   Ciphertext &ctxt_out) const;

    /// @brief Decrease the level of LWECiphertext by one
    /// @param ctxt
    /// @param ctxt_out
    void levelDownOne(const Ciphertext &ctxt, Ciphertext &ctxt_out) const;

private:
    ///@brief A context with which HomEvaluator is associated
    const Context context_;
    ///@brief Internal implementation object
    std::shared_ptr<HomEvaluatorImpl> impl_;
};

} // namespace HEaaN::LWE
