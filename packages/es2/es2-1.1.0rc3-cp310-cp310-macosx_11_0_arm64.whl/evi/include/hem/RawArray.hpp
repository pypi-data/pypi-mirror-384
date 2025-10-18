////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/device/Device.hpp"
#include "hem/impl/Serialize.hpp"
#include "hem/utils/AlignedAllocator.hpp"

#include <cstddef>
#include <cstring>
#include <filesystem>
#include <type_traits>

namespace hem {

template <typename T, typename = std::enable_if_t<std::is_pod_v<T>>>
class RawArray {
public:
    RawArray() = delete;
    RawArray(Device device);
    RawArray(Device device, size_t size, size_t aligned = DEFAULT_ALIGNMENT);
    RawArray(const RawArray &other);
    RawArray &operator=(const RawArray &other);
    RawArray(RawArray &&other) noexcept;
    RawArray &operator=(RawArray &&other) noexcept;
    ~RawArray();

    // Reallocate memory if the new size is larger than the current size
    // Otherwise, do nothing.
    void reallocate(size_t size, size_t aligned = 64);
    void deallocate();

    inline T &operator[](size_t idx) { return data_[idx]; }
    inline const T &operator[](size_t idx) const { return data_[idx]; }

    inline Device device() const { return device_; }
    inline size_t size() const { return size_; }
    inline T *data() { return data_; }
    inline const T *data() const { return data_; }

    template <class Archive>
    typename std::enable_if<
        std::is_base_of<cereal::PortableBinaryOutputArchive, Archive>::value,
        void>::type
    save(Archive &ar) const;

    template <class Archive>
    typename std::enable_if<
        std::is_base_of<cereal::PortableBinaryInputArchive, Archive>::value,
        void>::type
    load(Archive &ar);

    void save(const std::string &path) const {
        hem::Serialize::save(path, *this);
    }
    void save(const std::filesystem::path &path) const { save(path.string()); }
    void save(std::ostream &stream) const {
        hem::Serialize::save(stream, *this);
    }
    void load(const std::string &path) { hem::Serialize::load(path, *this); }
    void load(const std::filesystem::path &path) { load(path.string()); }
    void load(std::istream &stream) { hem::Serialize::load(stream, *this); }

private:
    void allocateWithoutCheck(size_t size, size_t aligned);

    const Device device_;
    size_t size_;
    size_t aligned_;
    T *data_;
};

template class RawArray<i8>;
template class RawArray<u8>;
template class RawArray<i32>;
template class RawArray<i64>;
template class RawArray<u32>;
template class RawArray<u64>;
template class RawArray<double>;
template class RawArray<u64 *>;
template class RawArray<const u64 *>;

} // namespace hem
