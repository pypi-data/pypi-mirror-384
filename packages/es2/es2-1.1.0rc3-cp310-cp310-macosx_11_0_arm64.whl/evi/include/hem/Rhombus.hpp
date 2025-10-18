////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Context.hpp"
#include "HEaaN/HomEvaluator.hpp"
#include "hem/DataType.hpp"
#include "hem/ModulusEngine.hpp"
#include "hem/RawArray.hpp"
#include "hem/device/Device.hpp"
#include "hem/utils/KeySwitcher.hpp"
#include "hem/utils/NTT.hpp"

namespace hem {

enum class RhombusMultType {
    RowMajor,
    ColumnMajor,
};

class Rhombus {
public:
    Rhombus(const HEaaN::Context &context, HEaaN::HomEvaluator &eval,
            double scale_factor, DeviceType device_type = DeviceType::CPU,
            hem::RhombusMultType mult_type = hem::RhombusMultType::RowMajor,
            bool use_preprocessed_ctxt = false);

    Rhombus(const HEaaN::Context &context, double scale_factor,
            DeviceType device_type = DeviceType::CPU,
            hem::RhombusMultType mult_type = hem::RhombusMultType::RowMajor,
            bool use_preprocessed_ctxt = false);

    Rhombus(const HEaaN::Context &context, HEaaN::HomEvaluator &eval,
            std::vector<HEaaN::RingSwitchKey> &switch_keys, double scale_factor,
            DeviceType device_type = DeviceType::CPU,
            hem::RhombusMultType mult_type = hem::RhombusMultType::RowMajor,
            bool use_preprocessed_ctxt = false);

    Rhombus(const HEaaN::Context &context,
            std::vector<HEaaN::RingSwitchKey> &switch_keys,
            DeviceType device_type = DeviceType::CPU,
            hem::RhombusMultType mult_type = hem::RhombusMultType::RowMajor,
            bool use_preprocessed_ctxt = false);

    void packToBlock(u64 r, u64 c, u64 *r_pack, u64 *c_pack) const;

    // automorphsim and multMonomial for plaintexts and ciphertexts
    void automorphismCPU(const u64 *op, u64 *res, const u64 sig,
                         const u64 level) const;

    void multMonomialCPU(const u64 *op, u64 *res, const u64 power,
                         const u64 level) const;

    void ExpandCPU(const hem::RawArray<u64> &ct_a,
                   const hem::RawArray<u64> &ct_b, hem::RawArray<u64> &exp_a,
                   hem::RawArray<u64> &exp_b);
    void ExpandGPU(const hem::RawArray<u64> &d_ct_a,
                   const hem::RawArray<u64> &d_ct_b,
                   hem::RawArray<u64> &d_exp_a, hem::RawArray<u64> &d_exp_b);

    std::vector<u64> NeedSwitchKeys() const;
    void SetSwitchKeys(const std::vector<HEaaN::RingSwitchKey> &switch_keys);

    std::vector<u64> NeedSwitchKeysCM() const;
    void SetSwitchKeysCM(const std::vector<HEaaN::RingSwitchKey> &switch_keys);

    // Preprocesses the whole matrix into plaintexts
    void PreprocessMatrix(const hem::RawArray<double> &W, const u64 r,
                          const u64 c, const u64 u, const u64 level = 0);

    void PreprocessMatrixRowMajor(const hem::RawArray<double> &W, const u64 r,
                                  const u64 c, const u64 u,
                                  const u64 level = 0);
    void PreprocessMatrixRowMajorCPU(const hem::RawArray<double> &W,
                                     const u64 r, const u64 c, const u64 u,
                                     const u64 level = 0);
    void PreprocessMatrixRowMajorGPU(const hem::RawArray<double> &W,
                                     const u64 r, const u64 c, const u64 u,
                                     const u64 level = 0);

    void PreprocessMatrixColumnMajor(const hem::RawArray<double> &W,
                                     const u64 r, const u64 c, const u64 u,
                                     const u64 level = 0);
    void PreprocessMatrixColumnMajorCPU(const hem::RawArray<double> &W, u64 r,
                                        u64 c, u64 u, const u64 level = 0);
    void PreprocessMatrixColumnMajorGPU(const hem::RawArray<double> &W, u64 r,
                                        u64 c, u64 u, const u64 level = 0);

    void PreprocessMatrix(const hem::RawArray<u64> &matrix, const u64 r,
                          const u64 c, const u64 u, const u64 level = 0);

    void PreprocessMatrixRowMajor(const hem::RawArray<u64> &matrix, const u64 r,
                                  const u64 c, const u64 u,
                                  const u64 level = 0);

    void PreprocessMatrixRowMajorCPU(const hem::RawArray<u64> &matrix,
                                     const u64 r, const u64 c, const u64 u,
                                     const u64 level = 0);

    void PreprocessMatrixRowMajorGPU(const hem::RawArray<u64> &matrix,
                                     const u64 r, const u64 c, const u64 u,
                                     const u64 level = 0);

    void PreprocessMatrixColumnMajor(const hem::RawArray<u64> &matrix,
                                     const u64 r, const u64 c, const u64 u,
                                     const u64 level = 0);

    void PreprocessMatrixColumnMajorCPU(const hem::RawArray<u64> &matrix,
                                        const u64 r, const u64 c, const u64 u,
                                        const u64 level = 0);

    void PreprocessMatrixColumnMajorGPU(const hem::RawArray<u64> &matrix,
                                        const u64 r, const u64 c, const u64 u,
                                        const u64 level = 0);

    void RhombusMVM(const std::vector<HEaaN::Ciphertext> &ctxt,
                    std::vector<HEaaN::Ciphertext> &ctxt_out);

    // Matrix Vector Multiplications - Row Major
    void RhombusRowMajorMVM(const std::vector<HEaaN::Ciphertext> &ctxt,
                            std::vector<HEaaN::Ciphertext> &ctxt_out);
    void RhombusRowMajorMVMCPU(const std::vector<HEaaN::Ciphertext> &ctxt,
                               std::vector<HEaaN::Ciphertext> &ctxt_out);
    void RhombusRowMajorMVMGPU(const std::vector<HEaaN::Ciphertext> &ctxt,
                               std::vector<HEaaN::Ciphertext> &ctxt_out);

    void RhombusRowMajorMVMBelowCPU(const hem::RawArray<u64> &d_ct_a_aut,
                                    const hem::RawArray<u64> &d_ct_b_aut,
                                    hem::RawArray<u64> &d_res_a,
                                    hem::RawArray<u64> &d_res_b,
                                    const u64 row_index);
    void RhombusRowMajorMVMBelowBundleGPU(const hem::RawArray<u64> &d_ct_a_aut,
                                          const hem::RawArray<u64> &d_ct_b_aut,
                                          hem::RawArray<u64> &d_res_a,
                                          hem::RawArray<u64> &d_res_b);

    void RhombusRowMajorMVMAbovePackRLWEsCPU(hem::RawArray<u64> &res_a,
                                             hem::RawArray<u64> &res_b,
                                             HEaaN::Ciphertext &ctxt_res);
    void RhombusRowMajorMVMAbovePackRLWEsBundleGPU(
        hem::RawArray<u64> &d_res_a, hem::RawArray<u64> &d_res_b,
        std::vector<HEaaN::Ciphertext> &ctxt_out);

    // Matrix Vector Multiplications - Column Major
    void RhombusColumnMajorMVM(const std::vector<HEaaN::Ciphertext> &ctxt,
                               std::vector<HEaaN::Ciphertext> &ctxt_out);
    void RhombusColumnMajorMVMCPU(const std::vector<HEaaN::Ciphertext> &ctxt,
                                  std::vector<HEaaN::Ciphertext> &ctxt_out);
    void RhombusColumnMajorMVMGPU(const std::vector<HEaaN::Ciphertext> &ctxt,
                                  std::vector<HEaaN::Ciphertext> &ctxt_out);

    void RhombusColumnMajorMVMBelowCPU(const hem::RawArray<u64> &ct_a_exp,
                                       const hem::RawArray<u64> &ct_b_exp,
                                       hem::RawArray<u64> &res_a,
                                       hem::RawArray<u64> &res_b,
                                       const u64 row_index);
    void
    RhombusColumnMajorMVMBelowBundleGPU(const hem::RawArray<u64> &d_ct_a_exp,
                                        const hem::RawArray<u64> &d_ct_b_cxp,
                                        hem::RawArray<u64> &d_res_a,
                                        hem::RawArray<u64> &d_res_b);

    void RhombusColumnMajorMVMAboveCPU(const hem::RawArray<u64> &res_a,
                                       const hem::RawArray<u64> &res_b,
                                       HEaaN::Ciphertext &ctxt_res);
    void RhombusColumnMajorMVMAboveBundleGPU(
        const hem::RawArray<u64> &res_a, const hem::RawArray<u64> &res_b,
        std::vector<HEaaN::Ciphertext> &ctxt_out);

    u64 getPreprocessedCtxtNum() const {
        return c_block_ * (mult_type_ == RhombusMultType::RowMajor
                               ? (1 << (u_ - h_))
                               : (degree_ / (1 << u_)));
    }
    u64 getU() const { return u_; }
    u64 getH() const { return h_; }

    hem::RawArray<u64> getMatrix() const { return matrix_; }

    u64 getNumHomMult() const { return num_hom_mult_; }
    u64 getNumKeySwitch() const { return num_key_switch_; }
    u64 getNumNTT() const { return num_ntt_; }
    double getKeySwitchTime() const { return key_switch_time_; }
    double getHomMultTime() const { return hom_mult_time_; }
    double getNTTTime() const { return ntt_time_; }

    RhombusMultType getMultType() const { return mult_type_; }

    void setScaleFactor(double scale_factor) { scale_factor_ = scale_factor; }

private:
    // Preprocesses a single block
    void PreprocessBlockCPU(const hem::RawArray<double> &W, const u64 row_idx,
                            const u64 col_idx);
    void PreprocessBlockGPU(const hem::RawArray<double> &W, const u64 row_idx,
                            const u64 col_idx);

    void PreprocessBlockColumnMajorCPU(const hem::RawArray<double> &W,
                                       const u64 row_idx, const u64 col_idx);
    void PreprocessBlockColumnMajorGPU(const hem::RawArray<double> &W,
                                       const u64 row_idx, const u64 col_idx);

    void SetSigToSwitchKeyIndex();
    void SetSigToSwitchKeyIndexCM();

    void AutomorphismInputCtxtsCPU(const hem::RawArray<u64> &ct_a,
                                   const hem::RawArray<u64> &ct_b,
                                   hem::RawArray<u64> &ct_a_aut,
                                   hem::RawArray<u64> &ct_b_aut);
    void AutomorphismInputCtxtsGPU(const hem::RawArray<u64> &d_ct_a,
                                   const hem::RawArray<u64> &d_ct_b,
                                   hem::RawArray<u64> &d_ct_a_aut,
                                   hem::RawArray<u64> &d_ct_b_aut);

    void RhombusRowMajorMVMEachRowBlockCPU(const hem::RawArray<u64> &ct_a_aut,
                                           const hem::RawArray<u64> &ct_b_aut,
                                           HEaaN::Ciphertext &ctxt_out,
                                           const u64 row_index);

    void RhombusColumnMajorMVMEachRowBlockCPU(
        const hem::RawArray<u64> &ct_a_exp, const hem::RawArray<u64> &ct_b_exp,
        HEaaN::Ciphertext &ctxt_out, const u64 row_index);

    const HEaaN::Context context_;
    const HEaaN::HomEvaluator eval_;
    std::vector<u64> sig_;
    std::vector<HEaaN::RingSwitchKey> switch_keys_;

    std::vector<u64> h_moduli_;
    hem::RawArray<u64> d_moduli_;

    // size constants of the matrix
    u64 r_, c_, u_, h_;
    u64 min_r_, min_c_;     // Size of a block
    u64 r_block_, c_block_; // Number of blocks
    u64 level_;

    double scale_factor_;

    DeviceType device_type_ = DeviceType::CPU;
    hem::RhombusMultType mult_type_ = hem::RhombusMultType::RowMajor;
    bool use_preprocessed_ctxt_ = false;

    hem::ModulusEngine engine_;
    hem::RawArray<u64> matrix_;

    hem::RawArray<u64> ct_pre_a_;
    hem::RawArray<u64> ct_pre_b_;
    hem::RawArray<u64> ct_res_a_;
    hem::RawArray<u64> ct_res_b_;

    hem::RawArray<u64> sig_arr;

    u64 degree_;
    u64 log_degree_;
    HEaaN::NTT::NTTArray ntts_;
    HEaaN::KeySwitcher::KeySwitcher keyswitcher_;

    double key_switch_time_ = 0;
    double hom_mult_time_ = 0;
    double ntt_time_ = 0;

    u64 num_key_switch_ = 0;
    u64 num_hom_mult_ = 0;
    u64 num_ntt_ = 0;
};

} // namespace hem
