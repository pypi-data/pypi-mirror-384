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
#include "HEaaN/MStoSSKeyBundle.hpp"
#include "HEaaN/Message.hpp"
#include "HEaaN/MultiSecretSwitchKeyBundle.hpp"
#include "HEaaN/SecretKey.hpp"

#include <optional>
#include <vector>
// #include "HEaaN/Interpolator.hpp"

namespace HEaaN {

class BootstrapperImpl;
class Device;
class HomEvaluator;
class Interpolator;
class RingSwitchKey;

///
///@brief A class consisting of bootstrap and its related functions
///
class HEAAN_API Bootstrapper {
public:
    ///@brief Constructs a class for boostrap.
    /// Pre-computation of bootstrapping constants is included.
    ///@param[in] eval HomEvaluator to be used for bootstrapping.
    ///@param[in] log_slots
    ///@param[in] use_min_keys Whether or not to use minimal rotation keys for
    /// bootstrap
    ///@details Without `log_slots` argument,
    /// it pre-compute the boot constants for full slots.
    explicit Bootstrapper(const HomEvaluator &eval, const u64 log_slots,
                          bool use_min_keys = false);
    explicit Bootstrapper(const HomEvaluator &eval, bool use_min_keys = false);

    ///@brief Constructs a class for boostrap which can perform sparse secret
    /// encapsulation, using the same Parameter as eval.
    /// Includes pre-computation of bootstrapping constants.
    ///@param[in] eval HomEvaluator to be used for bootstrapping.
    ///@param[in] context_sparse The context constructed with the corresponding
    /// sparse parameter of which eval was constructed.
    ///@param[in] log_slots Logarithm (base 2) of the number of plaintext slots.
    ///@param[in] use_min_keys Whether or not to use minimal rotation keys for
    /// bootstrap
    ///@details If the `log_slots` argument is not provided, the bootstrapping
    /// constants will be pre-computed for full slots.
    ///@throws RuntimeException if context_sparse is not a context constructed
    /// with the corresponding sparse parameter of which eval was constructed.
    /// Please refer to getSparseParameterPresetFor() for the sparse parameters.
    explicit Bootstrapper(const HomEvaluator &eval,
                          const Context &context_sparse, const u64 log_slots,
                          bool use_min_keys = false);
    explicit Bootstrapper(const HomEvaluator &eval,
                          const Context &context_sparse,
                          bool use_min_keys = false);

    ///@brief Check whether bootstrap is available
    ///@param[in] log_slots
    ///@details Check whether bootstrapping constants are pre-computed.
    /// These constants are necessary for the process of bootstrapping.
    bool isBootstrapReady(const u64 log_slots) const;

    ///@brief make the pre-computed data for bootstrapping
    ///@param[in] log_slots
    ///@throws RuntimeException if `log_slots` > (full log slots of this
    /// parameter)
    void makeBootConstants(const u64 log_slots);
    void makeBootConstants(const u64 log_slots,
                           const std::vector<u64> &log_dft_sizes) const;
    void makeBootConstants(const u64 log_slots,
                           const std::vector<u64> &log_dft_sizes,
                           const std::vector<u64> &levels,
                           std::optional<Real> cnst = std::nullopt) const;
    std::vector<std::vector<Message>>
    getMessageV0Diagonals(const u64 log_slots,
                          const std::vector<u64> &log_dft_sizes);

    ///@brief load the pre-computed data for bootstrapping to CPU/GPU memory
    ///@param[in] log_slots
    ///@param[in] device
    ///@details The pre-computed constants for bootstrapping are initially
    // loaded on CPU when performing makeBootConstants. To perform
    // bootstrap on Ciphertext on GPU memory, these constants should
    // be loaded on GPU. You may manually load the constants to reduce
    // latency of bootstrap. Otherwise, the first execution of bootstrap
    // on GPU will automatically load the constants on the device.
    ///@throws RuntimeException if boot constants are not pre-computed.
    void loadBootConstants(const u64 log_slots, const Device &device) const;

    void loadS2CConstants(const u64 log_slots, const Device &device) const;
    void loadC2SConstants(const u64 log_slots, const Device &device) const;

    void removeExceptS2CConstants(const u64 log_slots,
                                  const Device &device) const;
    void removeExceptC2SConstants(const u64 log_slots,
                                  const Device &device) const;

    ///@brief return the level right after (full slot) bootstrap
    u64 getLevelAfterFullSlotBootstrap() const;

    ///@brief return minimum level which is available to bootstrap
    u64 getMinLevelForBootstrap() const;

    ///@brief Bootstrap a Ciphertext with input range [-1, 1].
    ///@param[in] ctxt
    ///@param[out] ctxt_out
    ///@param[in] is_complex Set it to TRUE when the input ciphertext actually
    /// encrypting complex vectors.
    ///@details Recover the level of Ciphertext.
    ///@throws RuntimeException if level of ctxt is less than 3
    ///@throws RuntimeException if ctxt has nonzero rescale counter.
    void bootstrap(const Ciphertext &ctxt, Ciphertext &ctxt_out,
                   bool is_complex = false) const;

    void batchBootstrap(const std::vector<Ciphertext> &ctxts,
                        const MultiSecretSwitchKeyBundle &switch_keys,
                        const Interpolator &intp,
                        std::vector<Ciphertext> &ctxts_out,
                        bool conj_inv_out = false) const;

    void batchBootstrapExtended(const std::vector<Ciphertext> &ctxts,
                                const MultiSecretSwitchKeyBundle &switch_keys,
                                const Interpolator &intp,
                                std::vector<Ciphertext> &ctxts_out) const;

    void bootstrapMStoSS(const MSRLWECiphertext &ctxt,
                         const MStoSSKeyBundle &mstoss_keys,
                         const Interpolator &intp_to,
                         std::vector<Ciphertext> &ctxt_out) const;

    void bootstrapMStoSSOptimized(const MSRLWECiphertext &ctxt,
                                  const MStoSSKeyBundle &mstoss_keys,
                                  const Interpolator &intp_to,
                                  std::vector<Ciphertext> &ctxt_out) const;
    ///@brief Bootstrap a Ciphertext with two output Ciphertext, one for real
    /// part and the other for imaginary part.
    ///@param[in] ctxt
    ///@param[out] ctxt_out_real
    ///@param[out] ctxt_out_imag
    ///@details Recover the level of Ciphertexts.
    ///@throws RuntimeException if level of ctxt is less than 3
    ///@throws RuntimeException if ctxt has nonzero rescale counter.
    void bootstrap(const Ciphertext &ctxt, Ciphertext &ctxt_out_real,
                   Ciphertext &ctxt_out_imag, const Real cnst = 1.0) const;

    ///@brief Bootstrap a Ciphertext with larger input range [-2^20, 2^20].
    ///@param[in] ctxt
    ///@param[out] ctxt_out
    ///@param[in] is_complex Set it to TRUE when the input ciphertext actually
    /// encrypting complex vectors.
    ///@details Recover the level of Ciphertext. Note that this function is
    /// approximately two times slower than basic bootstrap function. Enabled
    /// only for FV and FG parameters.
    ///@throws RuntimeException if level of ctxt is less than 4
    ///@throws RuntimeException if ctxt has nonzero rescale counter.
    void bootstrapExtended(const Ciphertext &ctxt, Ciphertext &ctxt_out,
                           bool is_complex = false) const;

    ///@brief Bootstrap a Ciphertext with two output Ciphertext, one for real
    /// part and the other for imaginary part, with larger input range [-2^20,
    /// 2^20].
    ///@param[in] ctxt
    ///@param[out] ctxt_out_real
    ///@param[out] ctxt_out_imag
    ///@details Recover the level of Ciphertexts.
    ///@throws RuntimeException if level of ctxt is less than 4
    ///@throws RuntimeException if ctxt has nonzero rescale counter.
    void bootstrapExtended(const Ciphertext &ctxt, Ciphertext &ctxt_out_real,
                           Ciphertext &ctxt_out_imag) const;

    void batchBootstrap(const std::vector<Ciphertext> &ctxts,
                        const MultiSecretSwitchKeyBundle &switch_keys,
                        const Interpolator &intp,
                        std::vector<Ciphertext> &ctxts_out_real,
                        std::vector<Ciphertext> &ctxts_out_imag) const;

    void batchBootstrapExtended(const std::vector<Ciphertext> &ctxts,
                                const MultiSecretSwitchKeyBundle &switch_keys,
                                const Interpolator &intp,
                                std::vector<Ciphertext> &ctxts_out_real,
                                std::vector<Ciphertext> &ctxts_out_imag) const;

    void bootstrapMStoSS(const MSRLWECiphertext &ctxt,
                         const MStoSSKeyBundle &mstoss_keys,
                         const Interpolator &intp_to,
                         std::vector<Ciphertext> &ctxts_out_real,
                         std::vector<Ciphertext> &ctxts_out_imag) const;

    ///@brief Convert the slot-encoded ciphertext to the coeff-encoded
    /// ciphertext
    ///@param[in] ctxt
    ///@param[out] ctxt_out
    ///@throws RuntimeException if ctxt is coeff-encoded
    ///@throws RuntimeException if level of ctxt is less than 3
    void slotToCoeff(const Ciphertext &ctxt, Ciphertext &ctxt_out) const;

    void slotToCoeffSingleStep(const Ciphertext &ctxt, Ciphertext &ctxt_out,
                               std::pair<u64, u64> log_dft_size) const;

    void slotToCoeffSingleStepMSRLWE(const MSRLWECiphertext &ctxt,
                                     MSRLWECiphertext &ctxt_out,
                                     std::pair<u64, u64> log_dft_size) const;

    ///@brief Bootstrap a Ciphertext without slot-to-coeff process
    ///@param[in] ctxt
    ///@param[out] ctxt_out
    ///@param[in] is_complex Set it to TRUE when the input ciphertext encrypting
    /// complex vectors.
    ///@details The imaginary part of slot message corresponds to the later half
    /// of the coeff message. The coefficients of X^0, ..., X^(N/2 - 1) are real
    /// part, and the coefficients of X^(N/2), ..., X^(N - 1) are imaginary
    /// part. If is_complex = FALSE, then the function assumes that the later
    /// half coefficients are all zero.
    ///@throws RuntimeException if ctxt is slot-encoded
    ///@throws RuntimeException if ctxt has nonzero rescale counter
    void halfBoot(const Ciphertext &ctxt, Ciphertext &ctxt_out,
                  bool is_complex = true,
                  const bool conjugate_invariant_output = false) const;
    void halfBoot(const Ciphertext &ctxt, Ciphertext &ctxt_out_real,
                  Ciphertext &ctxt_out_imag) const;

    void integerToRootsBootstrap(const Ciphertext &ctxt,
                                 Ciphertext &ctxt_out) const;
    void integerToRootsBootstrap(const Ciphertext &ctxt,
                                 Ciphertext &ctxt_out_real,
                                 Ciphertext &ctxt_out_imag) const;
    /// @brief Enable accelerating RemoveI using conjugate-invariant ring
    /// @param context_embed : context for Z[X] / < X^2N + 1>
    /// @param ci_key : switch key to switch to conjugate-invariant sk for Z[X]
    /// / < X^N - 1 >
    /// @param intp_ci : Interpolator object constructed on Z[X] / < X^N - 1>
    void enableFastRemoveI(const Context &context_embed,
                           const Context &context_real,
                           const RingSwitchKey &to_ci_key,
                           const RingSwitchKey &from_ci_key,
                           const Interpolator &intp_ci);

    void enableFastRemoveIMSRLWE(const Context &context_embed,
                                 const Context &context_embed_ss,
                                 const Context &context_real,
                                 const RingSwitchKey &to_ci_key,
                                 const RingSwitchKey &from_ci_key,
                                 const Interpolator &intp_ci,
                                 const HomEvaluator &eval_ss);

    void enableOutsourcedFastRemoveIMSRLWE(
        const Context &context_ss_obts, const Context &context_embed_ms,
        const Context &context_embed_ss, const Context &context_real_ms,
        const RingSwitchKey &to_real_key, const RingSwitchKey &from_real_key,
        const Interpolator &intp_real_ss, const HomEvaluator &eval_ss);

    void enableConjInvOutput(const Context &context_out_real);

    ///@brief Get Context context
    const Context &getContext() const;

    ///@brief Enable outsourcing the RNS moduli used during bootstrapping
    ///@param btp_outsource
    ///@details By temporarily switching to and switching back from more compact
    /// moduli, the bootstrapping can be accelerated
    ///@throws RuntimeException if @p btp_outsource was not constructed with
    /// corresponding outsourcing parameter of which Bootstrapper was
    /// constructed. Please refer to getOutsourcingParameterPresetFor() for the
    /// outsourcing parameters.
    void enableOutsourcing(const Bootstrapper &btp_outsource);
    void enableOutsourcing(const Bootstrapper &btp_outsource,
                           const HomEvaluator &eval_ss);

    void setC2Suseminkey(bool set);
    bool getC2Suseminkey() const;

    bool getStatusUseMultiplyConstBeforeS2C() const;
    void setStatusUseMultiplyConstBeforeS2C(bool mult_b1);

    ////////////////////////////////////////////////////////////////////////////

private:
    std::shared_ptr<BootstrapperImpl> impl_;
};

} // namespace HEaaN
