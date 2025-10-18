////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/RawArray.hpp"
#include "hem/device/Device.hpp"
#include "hem/impl/Serialize.hpp"

#include <cstddef>
#include <filesystem>
#include <stdexcept>
#include <vector>

namespace hem {

template <typename T> class PTMatrix {
public:
    PTMatrix() = default;
    PTMatrix(const Device &device, u64 level, u64 scale_bits, size_t rows,
             size_t cols, size_t num_decomp, std::vector<u64> moduli);
    PTMatrix(const PTMatrix &other);
    PTMatrix &operator=(const PTMatrix &other);
    PTMatrix(PTMatrix &&other) noexcept;
    PTMatrix &operator=(PTMatrix &&other) noexcept;
    ~PTMatrix();

    inline std::vector<RawArray<T>> &array() { return data_; }
    inline const std::vector<RawArray<T>> &array() const { return data_; }
    inline T *data(size_t level) { return data_[level].data(); }
    inline const T *data(size_t level) const { return data_[level].data(); }
    inline u64 level() const { return level_; }
    inline void setLevel(u64 level) {
        if (level > level_) {
            throw std::invalid_argument(
                "New level must be less than or equal to the current level.");
        }
        level_ = level;
    }
    inline Device device() const {
        if (data_.empty()) {
            throw std::invalid_argument(
                "Cannot get device from empty PTMatrix.");
        }
        Device device = data_[0].device();
        for (size_t i = 1; i < data_.size(); i++) {
            if (data_[i].device() != device) {
                throw std::invalid_argument(
                    "All data levels must be on the same device.");
            }
        }
        return device;
    }

    inline const std::vector<u64> &moduli() const { return moduli_; }
    inline const u64 &modulus(size_t level) const { return moduli_[level]; }
    inline u64 scaleBits() const { return scale_bits_; }
    inline void setScaleBits(u64 scale_bits) { scale_bits_ = scale_bits; }
    inline size_t rows() const { return rows_; }
    inline size_t cols() const { return cols_; }
    inline size_t numDecomp() const { return num_decomp_; }

    template <class Archive,
              cereal::traits::DisableIf<cereal::traits::is_text_archive<
                  Archive>::value> = cereal::traits::sfinae>
    void save(Archive &ar) const;

    // After loaded, its type becomes `DeviceType::CPU`.
    template <class Archive,
              cereal::traits::DisableIf<cereal::traits::is_text_archive<
                  Archive>::value> = cereal::traits::sfinae>
    void load(Archive &ar);

private:
    std::vector<RawArray<T>> data_; // data_.size() = 1 + level
    std::vector<u64> moduli_;
    u64 level_;
    u64 scale_bits_;
    size_t rows_;
    size_t cols_;
    size_t num_decomp_;
    // Each raw array has the size of rows_ * cols_ * num_decomp_
    // (num_decomp_ = 1 for non-decomposed data)
};

template class PTMatrix<i8>;
template class PTMatrix<u8>;
template class PTMatrix<i32>;
template class PTMatrix<i64>;
template class PTMatrix<u64>;
template class PTMatrix<u64 *>;
template class PTMatrix<double>;

class PTMatrixBuilder {
public:
    PTMatrixBuilder() = default;
    inline PTMatrixBuilder &setDevice(const Device &device) {
        device_ = device;
        return *this;
    }
    inline PTMatrixBuilder &setModuli(const std::vector<u64> &moduli) {
        moduli_ = moduli;
        return *this;
    }
    inline PTMatrixBuilder &setLevel(u64 level) {
        level_ = level;
        return *this;
    }
    inline PTMatrixBuilder &setScaleBits(u64 scale_bits) {
        scale_bits_ = scale_bits;
        return *this;
    }
    inline PTMatrixBuilder &setShape(size_t rows, size_t cols) {
        rows_ = rows;
        cols_ = cols;
        return *this;
    }
    inline PTMatrixBuilder &setNumDecomp(size_t num_decomp) {
        num_decomp_ = num_decomp;
        return *this;
    }
    template <typename T> inline PTMatrix<T> build() {
        return PTMatrix<T>(device_, level_, scale_bits_, rows_, cols_,
                           num_decomp_, moduli_);
    }

private:
    Device device_ = Device(DeviceType::CPU);
    std::vector<u64> moduli_ = {};
    u64 level_ = 0;
    u64 scale_bits_ = 0;
    size_t rows_ = 0;
    size_t cols_ = 0;
    size_t num_decomp_ = 0;
};

// TODO: make smart way
template <typename T> class CTMatrix {
public:
    CTMatrix() = default;

    inline u64 level() const {
        throwIfEmpty();
        u64 level = (data_)[0].level();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].level() != level) {
                throw std::invalid_argument(
                    "All data levels must have the same level.");
            }
        }
        return level;
    }
    inline void setLevel(u64 level) {
        throwIfEmpty();
        for (size_t i = 0; i < data_.size(); i++) {
            (data_)[i].setLevel(level);
        }
    }
    inline Device device() const {
        throwIfEmpty();
        Device device = (data_)[0].device();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].device() != device) {
                throw std::invalid_argument(
                    "All data levels must be on the same device.");
            }
        }
        return device;
    }
    inline const std::vector<u64> &moduli() const {
        throwIfEmpty();
        const std::vector<u64> &moduli = (data_)[0].moduli();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].moduli() != moduli) {
                throw std::invalid_argument(
                    "All data levels must have the same moduli.");
            }
        }
        return moduli;
    }
    inline const u64 &modulus(size_t level) const {
        throwIfEmpty();
        const u64 &modulus = (data_)[0].modulus(level);
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].modulus(level) != modulus) {
                throw std::invalid_argument(
                    "All data levels must have the same modulus.");
            }
        }
        return modulus;
    }
    inline u64 scaleBits() const {
        throwIfEmpty();
        u64 scale_bits = (data_)[0].scaleBits();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].scaleBits() != scale_bits) {
                throw std::invalid_argument(
                    "All data levels must have the same scale bits.");
            }
        }
        return scale_bits;
    }
    inline void setScaleBits(u64 scale_bits) {
        throwIfEmpty();
        for (size_t i = 0; i < data_.size(); i++) {
            (data_)[i].setScaleBits(scale_bits);
        }
    }
    inline size_t rows() const {
        throwIfEmpty();
        size_t rows = (data_)[0].rows();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].rows() != rows) {
                throw std::invalid_argument(
                    "All data levels must have the same number of rows.");
            }
        }
        return rows;
    }
    inline size_t cols() const {
        throwIfEmpty();
        size_t cols = (data_)[0].cols();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].cols() != cols) {
                throw std::invalid_argument(
                    "All data levels must have the same number of columns.");
            }
        }
        return cols;
    }
    inline size_t numDecomp() const {
        throwIfEmpty();
        size_t num_decomp = (data_)[0].numDecomp();
        for (size_t i = 1; i < data_.size(); i++) {
            if ((data_)[i].numDecomp() != num_decomp) {
                throw std::invalid_argument("All data levels must have the "
                                            "same number of decompositions.");
            }
        }
        return num_decomp;
    }

    void save(const std::string &path) const {
        hem::Serialize::save(path, data_);
    }
    void save(const std::filesystem::path &path) const { save(path.string()); }
    void save(std::ostream &stream) const {
        hem::Serialize::save(stream, data_);
    }
    void load(const std::string &path) { hem::Serialize::load(path, data_); }
    void load(const std::filesystem::path &path) { load(path.string()); }

    void load(std::istream &stream) { hem::Serialize::load(stream, data_); }

    PTMatrix<T> &data(size_t idx) { return data_[idx]; }
    const PTMatrix<T> &data(size_t idx) const { return data_[idx]; }
    T *data(size_t idx, size_t level) { return data_[idx].data(level); }
    const T *data(size_t idx, size_t level) const {
        return data_[idx].data(level);
    }

    size_t numPTMatrix() const { return data_.size(); }
    void resize(size_t num_pt_matrix) {
        if (num_pt_matrix == 0) {
            throw std::invalid_argument("Number of PTMatrix must be > 0.");
        }
        data_.resize(num_pt_matrix);
    }
    void clear() { data_.clear(); }

private:
    std::vector<PTMatrix<T>> data_ = {};
    void throwIfEmpty() const {
        if (data_.empty()) {
            throw std::invalid_argument("CTMatrix is empty.");
        }
    }

    void throwIfIndexOutOfBounds(size_t index) const {
        if (index >= data_.size()) {
            throw std::out_of_range("Index " + std::to_string(index) +
                                    " is out of bounds for CTMatrix of size " +
                                    std::to_string(data_.size()));
        }
    }
};

template class CTMatrix<i8>;
template class CTMatrix<u8>;
template class CTMatrix<i32>;
template class CTMatrix<i64>;
template class CTMatrix<u64>;
template class CTMatrix<u64 *>;
template class CTMatrix<double>;

class CTMatrixBuilder {
public:
    CTMatrixBuilder() { setNumPTMatrix(2); }
    inline CTMatrixBuilder &setNumPTMatrix(size_t num_pt_matrix) {
        num_pt_matrix_ = num_pt_matrix;
        pt_matrix_builders_.resize(num_pt_matrix_);
        return *this;
    }
    inline CTMatrixBuilder &setDevice(const Device &device) {
        device_ = device;
        for (auto &builder : pt_matrix_builders_) {
            builder.setDevice(device_);
        }
        return *this;
    }
    inline CTMatrixBuilder &setModuli(const std::vector<u64> &moduli) {
        for (auto &builder : pt_matrix_builders_) {
            builder.setModuli(moduli);
        }
        return *this;
    }
    inline CTMatrixBuilder &setLevel(u64 level) {
        for (auto &builder : pt_matrix_builders_) {
            builder.setLevel(level);
        }
        return *this;
    }
    inline CTMatrixBuilder &setScaleBits(u64 scale_bits) {
        for (auto &builder : pt_matrix_builders_) {
            builder.setScaleBits(scale_bits);
        }
        return *this;
    }
    inline CTMatrixBuilder &setShape(size_t rows, size_t cols) {
        for (auto &builder : pt_matrix_builders_) {
            builder.setShape(rows, cols);
        }
        return *this;
    }
    inline CTMatrixBuilder &setNumDecomp(size_t num_decomp) {
        for (auto &builder : pt_matrix_builders_) {
            builder.setNumDecomp(num_decomp);
        }
        return *this;
    }

    // Setters for individual PTMatrix
    inline CTMatrixBuilder &setLevel(size_t index, u64 level) {
        if (index >= num_pt_matrix_) {
            throw std::out_of_range("Index out of range");
        }
        pt_matrix_builders_[index].setLevel(level);
        return *this;
    }
    inline CTMatrixBuilder &setScaleBits(size_t index, u64 scale_bits) {
        if (index >= num_pt_matrix_) {
            throw std::out_of_range("Index out of range");
        }
        pt_matrix_builders_[index].setScaleBits(scale_bits);
        return *this;
    }
    inline CTMatrixBuilder &setShape(size_t index, size_t rows, size_t cols) {
        if (index >= num_pt_matrix_) {
            throw std::out_of_range("Index out of range");
        }
        pt_matrix_builders_[index].setShape(rows, cols);
        return *this;
    }
    inline CTMatrixBuilder &setNumDecomp(size_t index, size_t num_decomp) {
        if (index >= num_pt_matrix_) {
            throw std::out_of_range("Index out of range");
        }
        pt_matrix_builders_[index].setNumDecomp(num_decomp);
        return *this;
    }

    inline CTMatrixBuilder &setPTMatrix(size_t index,
                                        const PTMatrixBuilder &builder) {
        if (index >= num_pt_matrix_) {
            throw std::out_of_range("Index out of range");
        }
        pt_matrix_builders_[index] = builder;
        return *this;
    }

    template <typename T> inline CTMatrix<T> build() {
        CTMatrix<T> ct_matrix;
        ct_matrix.resize(num_pt_matrix_);
        for (size_t i = 0; i < num_pt_matrix_; i++) {
            ct_matrix.data(i) = pt_matrix_builders_[i].build<T>();
        }
        return ct_matrix;
    }

private:
    std::vector<PTMatrixBuilder> pt_matrix_builders_;
    Device device_ = Device(DeviceType::CPU);
    size_t num_pt_matrix_ = 0;
};

} // namespace hem
