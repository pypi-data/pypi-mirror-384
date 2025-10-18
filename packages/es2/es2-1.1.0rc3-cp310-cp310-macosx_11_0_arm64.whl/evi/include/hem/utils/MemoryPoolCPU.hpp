////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <cstddef>
#include <cstdlib>
#include <utility>

namespace hem {

// TODO: Make smarter memory pool
class MemoryPoolCPU {
public:
    MemoryPoolCPU(const MemoryPoolCPU &) = delete;
    MemoryPoolCPU &operator=(const MemoryPoolCPU &) = delete;

    static void *getDataA(size_t size) {
        return getInstance()->getAllocatedDataA(size);
    }

    static void *getDataB(size_t size) {
        return getInstance()->getAllocatedDataB(size);
    }

    static void *getDataC(size_t size) {
        return getInstance()->getAllocatedDataC(size);
    }

private:
    std::pair<size_t, void *> a_data_;
    std::pair<size_t, void *> b_data_;
    std::pair<size_t, void *> c_data_;

    inline static MemoryPoolCPU *getInstance() {
        static MemoryPoolCPU instance;
        return &instance;
    }

    MemoryPoolCPU() {
        a_data_ = std::make_pair(0, nullptr);
        b_data_ = std::make_pair(0, nullptr);
        c_data_ = std::make_pair(0, nullptr);
    }

    ~MemoryPoolCPU() {
        if (a_data_.first != 0) {
            std::free(a_data_.second);
            a_data_.second = nullptr;
            a_data_.first = 0;
        }
        if (b_data_.first != 0) {
            std::free(b_data_.second);
            b_data_.second = nullptr;
            b_data_.first = 0;
        }
        if (c_data_.first != 0) {
            std::free(c_data_.second);
            c_data_.second = nullptr;
            c_data_.first = 0;
        }
    }

    void *getAllocatedDataA(size_t size) {
        if (a_data_.first < size) {
            if (a_data_.first != 0) {
                std::free(a_data_.second);
            }
            a_data_.first = size;
            a_data_.second = static_cast<void *>(std::malloc(size));
        }
        return a_data_.second;
    }

    void *getAllocatedDataB(size_t size) {
        if (b_data_.first < size) {
            if (b_data_.first != 0) {
                std::free(b_data_.second);
            }
            b_data_.first = size;
            b_data_.second = static_cast<void *>(std::malloc(size));
        }
        return b_data_.second;
    }

    void *getAllocatedDataC(size_t size) {
        if (c_data_.first < size) {
            if (c_data_.first != 0) {
                std::free(c_data_.second);
            }
            c_data_.first = size;
            c_data_.second = static_cast<void *>(std::malloc(size));
        }
        return c_data_.second;
    }
};

} // namespace hem
