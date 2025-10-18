////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "HEaaN/Ciphertext.hpp"
#include "HEaaN/Context.hpp"
#include "HEaaN/Decryptor.hpp"
#include "HEaaN/Encryptor.hpp"
#include "HEaaN/KeyPack.hpp"
#include "HEaaN/SecretKey.hpp"
#include "hem/DataType.hpp"

namespace hem {

class MatrixEnDecryptor {
public:
    MatrixEnDecryptor(HEaaN::Context context);

    void deviceTo(std::vector<HEaaN::Ciphertext> &ctxt_database,
                  const HEaaN::Device &device) const;

    void encryptMatrix(const double *database, u64 K, u64 N,
                       const HEaaN::SecretKey &sk,
                       std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
                       double scale_factor, bool ntt_output) const;

    void encryptMatrix(const double *database, u64 K, u64 N,
                       const HEaaN::KeyPack &pack,
                       std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
                       double scale_factor, bool ntt_output) const;

    void encryptPackedMatrix(const double *database, u64 K, u64 N,
                             const HEaaN::SecretKey &sk,
                             std::vector<HEaaN::Ciphertext> &ctxt_database,
                             u64 level, double scale_factor, bool ntt_output,
                             const u64 degree_lo = 0) const;

    void encryptVector(const double *vec, u64 N, const HEaaN::SecretKey &sk,
                       std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
                       double scale_factor, bool ntt_output) const;

    void encryptVectorWithAutomorphismPreprocessing(
        const double *vec, u64 N, const HEaaN::SecretKey &sk,
        std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
        double scale_factor, bool ntt_output, const u64 u_, const u64 h_) const;

    void encryptVectorWithExpandPreprocessing(
        const double *vec, u64 N, const HEaaN::SecretKey &sk,
        std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
        double scale_factor, bool ntt_output, const u64 u_) const;

    void decryptMatrix(const std::vector<HEaaN::Ciphertext> &ctxt_database,
                       const HEaaN::SecretKey &sk, double *database, u64 K,
                       u64 N, double scale_factor, bool ntt_output) const;

    void
    decryptPackedMatrix(const std::vector<HEaaN::Ciphertext> &ctxt_database,
                        const HEaaN::SecretKey &sk, double *database, u64 K,
                        u64 N, double scale_factor, bool ntt_output,
                        const u64 degree_lo = 0) const;

    void decryptVector(const std::vector<HEaaN::Ciphertext> &ctxt_database,
                       const HEaaN::SecretKey &sk, double *database, u64 N_pack,
                       u64 N, double scale_factor, u64 step,
                       bool ntt_output) const;

    const HEaaN::Context &getContext() const { return context_; }

private:
    const HEaaN::Context context_;

    const HEaaN::Encryptor enc_;
    const HEaaN::Decryptor dec_;

    void convertColumnMajorMatrixToRowMajorRLWEMsgs(
        const double *database, u64 K, u64 N,
        std::vector<HEaaN::CoeffMessage> &msg_database) const;

    void convertColumnMajorMatrixToPackedColumnMajorRLWEMsgs(
        const double *database, u64 K, u64 N,
        std::vector<HEaaN::CoeffMessage> &msg_database,
        const u64 degree_lo) const;

    void convertVectorToRLWEMsgs(
        const double *vec, u64 N,
        std::vector<HEaaN::CoeffMessage> &msg_database) const;

    void
    PreprocessAutomorphismVector(const double *vec, u64 N,
                                 std::vector<HEaaN::CoeffMessage> &msg_database,
                                 const u64 u_, const u64 h_) const;

    void PreprocessExpandVector(const double *vec, u64 N,
                                std::vector<HEaaN::CoeffMessage> &msg_database,
                                const u64 u_) const;

    void encryptMatrix(std::vector<HEaaN::CoeffMessage> &msg_database,
                       const HEaaN::SecretKey &sk,
                       std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
                       double scale_factor, bool ntt_output) const;

    void encryptMatrix(std::vector<HEaaN::CoeffMessage> &msg_database,
                       const HEaaN::KeyPack &pack,
                       std::vector<HEaaN::Ciphertext> &ctxt_database, u64 level,
                       double scale_factor, bool ntt_output) const;

    void convertRowMajorRLWEMsgsToColumnMajorMatrix(
        const std::vector<HEaaN::CoeffMessage> &msg_database, double *database,
        u64 K, u64 N) const;

    void convertPackedColumnMajorRLWEMsgsToColumnMajorMatrix(
        const std::vector<HEaaN::CoeffMessage> &msg_database, double *database,
        u64 K, u64 N, const u64 degree_lo) const;

    void convertRLWEMsgsToVector(
        const std::vector<HEaaN::CoeffMessage> &msg_database, double *database,
        u64 N_pack, u64 N, u64 step) const;

    void decryptMatrix(const std::vector<HEaaN::Ciphertext> &ctxt_database,
                       const HEaaN::SecretKey &sk,
                       std::vector<HEaaN::CoeffMessage> &msg_database,
                       double scale_factor, bool ntt_output) const;
};

} // namespace hem
