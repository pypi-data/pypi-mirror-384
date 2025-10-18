////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2024, CryptoLab Inc. All rights reserved.               //
// This software and/or source code may be commercially used and/or           //
// disseminated only with the written permission of CryptoLab Inc,            //
// or in accordance with the terms and conditions stipulated in the           //
// agreement/contract under which the software and/or source code has been    //
// supplied by CryptoLab Inc. Any unauthorized commercial use and/or          //
// dissemination of this file is strictly prohibited and will constitute      //
// an infringement of copyright.                                              //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "EVI/impl/Type.hpp"

#include "EVI/Enums.hpp"
#include "EVI/impl/CKKSTypes.hpp"
#include "EVI/impl/ContextImpl.hpp"
#include "EVI/impl/KeyPackImpl.hpp"
#include "utils/CheckMacros.hpp"
#include "utils/CudaUtils.hpp"
#include "utils/Exceptions.hpp"
// #include "EVI/Evaluator.hpp"
#include <cstdint>
#include <iostream>
#include <memory>
#include <optional>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>
#include <vector>

namespace evi {
namespace detail {
template <DeviceType D, DataType T, EvalMode M>
class IndexBase;

template <DataType T, EvalMode M>
class IndexBase<DeviceType::CPU, T, M> {

public:
    IndexBase() = delete;
    IndexBase(const Context &context);

    void setData(DataState data, std::optional<KeyPack> keypack = std::nullopt);
    void store(const std::string &dir_path);
    void load(const std::string &dir_path);
    void serializeTo(std::ostream &stream);
    void deserializeFrom(std::istream &stream);
    void append(const Query::SingleQuery item);
    std::vector<u64> appendV2(const Query::SingleQuery item);

    const Context &getContext() const {
        return context_;
    }

    DataState &getData() {
        return state_;
    }
    polydata getPolyData(const int pos, const int level, std::optional<int> idx = std::nullopt) {
        return state_->getPolyData(pos, level);
    };
    u32 getItemCount() const {
        return n_;
    }
    int getLevel() const {
        return is_lv1_ ? 1 : 0;
    }
    u32 getPadRank() const {
        return pad_rank_;
    }

    u32 getPoorIndex() const {
        return poor_batch_idx_;
    }

    void toSharedA(const KeyPack &keypack);

#ifdef BUILD_WITH_HEM
public:
    void setMatrices(Query query);

    const std::vector<std::shared_ptr<hem::CTMatrix<u64>>> &getAllMatrices() const {
        return matrices_;
    }

    const hem::CTMatrix<u64> &getMatrix(size_t idx) const {
        if (idx >= matrices_.size()) {
            throw std::out_of_range("Matrix index out of range");
        }
        return *matrices_[idx];
    }

    void serializeMatrixTo(std::ostream &os);
    void deserializeMatrixFrom(std::istream &is);

private:
    std::vector<std::shared_ptr<hem::CTMatrix<u64>>> matrices_;
#endif

protected:
    const Context context_;
    DataState state_;

    u32 log_pad_rank_;
    u32 pad_rank_;
    u32 rank_;

    u32 num_batch_;
    u32 n_;
    i32 max_id_;
    u32 items_per_ctxt_;
    u32 pad_max_id_;
    u32 num_append_to_gpu_;

    u32 gpu_upload_target_ = 0;
    u32 poor_batch_idx_ = 0;

    bool is_lv1_;
    bool full_shared_a_;
};

#ifdef BUILD_WITH_CUDA

template <DataType T, EvalMode M>
class IndexBase<DeviceType::GPU, T, M> : public IndexBase<DeviceType::CPU, T, M> {
public:
    IndexBase(const Context &context, std::optional<int> target_device_id = std::nullopt);
    ~IndexBase();

    void loadToGpu();
    void freeGpuForDB();
    void appendItemGPU();
    // void loadToGpu();
    // void loadCtxtOnly();
    // void appendCtxtOnly();

    std::vector<int> &getBatchListOfDeviceId(const int device_id) {
        return batch_index_per_device[device_id];
    }

    bool isLoadedToGPU(const int device_id) {
        return is_gpu_db_loaded_[device_id];
    }

    polydata &getPolyData(const int pos, const int level, std::optional<int> idx = std::nullopt);

private:
    DeviceData<T> data;

    void initialize();
    void extendBatchGpu(int num_extend);
    void mallocBatch(const int batch_index, u32 size);
    void memcpyBatch(const int batch_index, const int batch_offset, const int offset, u64 size);
    void freeBatch(const int batch_index);
    void freeGpuForBatch(const int device_id);

    DeviceIds device_ids_;
    int device_id_;
    int num_gpu_;
    int device_offset;
    bool db_loaded_ = false;

    std::unordered_map<int, bool> is_gpu_db_loaded_;
    std::unordered_map<int, std::vector<int>> batch_index_per_device;

    bool isGpuMemAlloced = false;

#ifdef BUILD_WITH_HEM
public:
    void setMatrices(Query query);

    const std::vector<std::shared_ptr<hem::CTMatrix<u64>>> &getAllMatrices() const {
        return matrices_;
    }

    const hem::CTMatrix<u64> &getMatrix(size_t idx) const {
        if (idx >= matrices_.size()) {
            throw std::out_of_range("Matrix index out of range");
        }
        return *matrices_[idx];
    }

    void serializeMatrixTo(std::ostream &os);
    void deserializeMatrixFrom(std::istream &is);

private:
    std::vector<std::shared_ptr<hem::CTMatrix<u64>>> matrices_;
#endif
};
#endif // BUILD_WITH_CUDA
} // namespace detail
} // namespace evi
