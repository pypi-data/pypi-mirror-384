////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once
// TODO: Remove this file and use the original file from HEAAN library.
// This is a modified version for only level 0 of HEAAN/src/impl/KeySwitcher.cpp

#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Context.hpp"
#include "HEaaN/HomEvaluator.hpp"
#include "HEaaN/RingSwitchKey.hpp"
#include "hem/DataType.hpp"
#include "hem/ModulusEngine.hpp"
#include "hem/ModulusMatrix.hpp"
#include "hem/RawArray.hpp"
#include "hem/device/Device.hpp"
#include "hem/utils/NTT.hpp"

namespace HEaaN::KeySwitcher {

class KeySwitcher {
public:
    KeySwitcher(const Context &context, hem::DeviceType device_type);

    void SetSwitchKeys(std::vector<hem::u64> &sig,
                       std::vector<HEaaN::RingSwitchKey> &switch_keys);
    void SetSwitchKeysGPU(std::vector<hem::u64> &sig,
                          std::vector<HEaaN::RingSwitchKey> &switch_keys);

    void modUpCPU(const u64 *op, u64 *res, const u64 level) const;
    void modUpCPU(const u64 **op, u64 *res, const u64 level) const;
    void modUpGPU(const u64 *op, u64 *res, const u64 num_poly, const u64 level);
    void modUpGPU(const u64 **op, u64 *res, const u64 num_poly,
                  const u64 level);

    void modDownCPU(const u64 *op_a, const u64 *op_b, u64 *res_a, u64 *res_b,
                    const u64 level, bool ntt_output = false) const;
    void modDownCPU(const u64 *op_a, const u64 *op_b, u64 **res_a, u64 **res_b,
                    const u64 level, bool ntt_output = false) const;
    void modDownGPU(const u64 *op_a, const u64 *op_b, u64 *res_a, u64 *res_b,
                    const u64 num_poly, const u64 level,
                    bool ntt_output = false);
    void modDownGPU(const u64 *op_a, const u64 *op_b, u64 **res_a, u64 **res_b,
                    const u64 num_poly, const u64 level,
                    bool ntt_output = false);

    void multEvalKeyCPU(const u64 *poly_modup, HEaaN::RingSwitchKey &eval_key,
                        u64 *res_a, u64 *res_b, const u64 level) const;
    void multEvalKeyGPU(const u64 *poly_modup, HEaaN::RingSwitchKey &eval_key,
                        u64 *res_a, u64 *res_b, const u64 num_poly,
                        const u64 level);
    void multEvalKeySigGPU(const u64 *poly_modup, u64 sig, u64 *res_a,
                           u64 *res_b, const u64 num_poly, const u64 level);
    void multDifferentEvalKeyGPU(const u64 *poly_modup, const u64 *sig_arr,
                                 u64 *res_a, u64 *res_b, const u64 num_poly,
                                 const u64 level);

    void switchKey(const Ciphertext &ctxt, RingSwitchKey &switch_key,
                   Ciphertext &ctxt_out, bool ntt_output = false);
    void switchKey(const Ciphertext &ctxt, const hem::u64 sig,
                   Ciphertext &ctxt_out, bool ntt_output = false);
    void switchKey(const hem::u64 *op_a, const hem::u64 *op_b,
                   RingSwitchKey &switch_key, hem::u64 *res_a, hem::u64 *res_b,
                   bool ntt_output = false);
    void switchKey(const hem::u64 *op_a, const hem::u64 *op_b,
                   const hem::u64 sig, hem::u64 *res_a, hem::u64 *res_b,
                   bool ntt_output = false);
    void switchKey(const u64 *op_a, const u64 *op_b, RingSwitchKey &switch_key,
                   u64 *res_a, u64 *res_b, const u64 level,
                   bool ntt_output = false);
    void switchKey(const u64 *op_a, const u64 *op_b, const u64 sig, u64 *res_a,
                   u64 *res_b, const u64 level, bool ntt_output = false);
    void switchKeyCPU(const u64 **op_a, const u64 **op_b,
                      HEaaN::RingSwitchKey &eval_key, u64 **res_a, u64 **res_b,
                      const u64 level, bool ntt_output = false);
    void switchKeyCPU(const hem::CTMatrix<u64> &op,
                      HEaaN::RingSwitchKey &eval_key, hem::CTMatrix<u64> &res,
                      const u64 idx_poly, const u64 level,
                      bool ntt_output = false);
    void switchKeyCPU(const hem::CTMatrix<u64> &op, const u64 sig,
                      hem::CTMatrix<u64> &res, const u64 idx_poly,
                      const u64 level, bool ntt_output = false);

    void switchKeyBatch(const u64 *op_a, const u64 *op_b,
                        RingSwitchKey &switch_key, u64 *res_a, u64 *res_b,
                        const u64 num_poly, const u64 level,
                        bool ntt_output = false);
    void switchKeyBatch(const u64 *op_a, const u64 *op_b, const u64 sig,
                        u64 *res_a, u64 *res_b, const u64 num_poly,
                        const u64 level, bool ntt_output = false);
    void switchKeyBatch(const u64 *op_a, const u64 *op_b, const u64 *sig_arr,
                        u64 *res_a, u64 *res_b, const u64 num_poly,
                        const u64 level, bool ntt_output = false);
    void switchKeyBatchGPU(const u64 **op_a, const u64 **op_b,
                           const u64 *sig_arr, u64 **res_a, u64 **res_b,
                           const u64 num_poly, const u64 level,
                           bool ntt_output = false);
    void switchKeyBatchGPU(const hem::CTMatrix<u64> &op, const u64 *sig_arr,
                           hem::CTMatrix<u64> &res, const u64 num_poly,
                           const u64 level, bool ntt_output = false);
    void switchKeyBatchGPU(const u64 **op_a, const u64 **op_b,
                           RingSwitchKey &switch_key, u64 **res_a, u64 **res_b,
                           const u64 num_poly, const u64 level,
                           bool ntt_output = false);
    void switchKeyBatchGPU(const hem::CTMatrix<u64> &op,
                           RingSwitchKey &switch_key, hem::CTMatrix<u64> &res,
                           const u64 num_poly, const u64 level,
                           bool ntt_output = false);

    void rescaleCiphertext(HEaaN::Ciphertext &ctxt);
    void rescaleCPU(const hem::CTMatrix<u64> &op, hem::CTMatrix<u64> &res,
                    const u64 idx_poly, const u64 level);
    void rescaleCPU(const u64 **op, u64 **res, const u64 level);
    void rescaleBatchCPU(const hem::CTMatrix<u64> &op, hem::CTMatrix<u64> &res,
                         const u64 num_poly);
    void rescaleBatchGPU(const hem::CTMatrix<u64> &op, hem::CTMatrix<u64> &res,
                         const u64 num_poly);
    void rescaleBatchGPU(const u64 **op, u64 **res, const u64 num_poly,
                         const u64 level);

    HEaaN::RingSwitchKey getSwitchKey(hem::u64 sig) const {
        return switch_keys_[sig_[sig]];
    }

    const Context &getContext() const { return context_; }
    const HomEvaluator &getEvaluator() const { return eval_; }

    void reallocateGPU(const u64 num_poly);

private:
    const Context context_;
    const HomEvaluator eval_;

    const hem::DeviceType device_type_;
    const hem::Device device_;

    hem::RawArray<hem::u64> sig_;
    std::vector<HEaaN::RingSwitchKey> switch_keys_;

    const u64 degree_, log_degree_;
    const u64 encrypt_level_;
    const u64 length_, xlength_, dnum_, alpha_;
    std::vector<u64> moduli_;

    HEaaN::NTT::NTTArray ntts_;

    hem::RawArray<u64> switch_key_a, switch_key_b;
    hem::RawArray<u64> switch_key_a_single, switch_key_b_single;
    hem::RawArray<u64> d_tmp_a, d_tmp_b;
    hem::RawArray<u64> d_tmp_modup, d_tmp_bx;
    hem::RawArray<u64> d_tmp_res_a, d_tmp_res_b;

    hem::ModulusEngine engine_;

    hem::RawArray<u64> h_hat_q_inv_mod_;
    hem::RawArray<u64> h_mod_up_hat_inverse_mod_start_,
        h_mod_down_hat_inverse_mod_start_;
    std::vector<hem::RawArray<u64>> h_mod_up_hat_mod_end_,
        h_mod_down_hat_mod_end_;
    std::vector<hem::RawArray<u64>> h_rescale_inv_mod_;
    hem::RawArray<u64> barr_for_64_;
    hem::RawArray<u64> mod_down_prod_inverse_;

    void modUpCPU(const u64 **op, u64 *res, const u64 level, u64 *tmp_ptr_a,
                  u64 *tmp_ptr_b) const;
    void modDownCPU(const u64 *op_a, const u64 *op_b, u64 **res_a, u64 **res_b,
                    const u64 level, bool ntt_output, u64 *tmp_ptr_a,
                    u64 *tmp_ptr_b) const;
};

} // namespace HEaaN::KeySwitcher
