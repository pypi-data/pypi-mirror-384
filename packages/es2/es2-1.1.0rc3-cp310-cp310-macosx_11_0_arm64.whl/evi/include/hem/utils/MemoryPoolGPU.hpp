////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DeviceMemory.hpp"

#include <cstddef>
#include <utility>

namespace hem {

// TODO: Make smarter memory pool
class MemoryPoolGPU {
public:
    MemoryPoolGPU(const MemoryPoolGPU &) = delete;
    MemoryPoolGPU &operator=(const MemoryPoolGPU &) = delete;

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

    static MemoryPoolGPU *getInstance() {
        static MemoryPoolGPU instance;
        return &instance;
    }

    MemoryPoolGPU() {
        a_data_ = std::make_pair(0, nullptr);
        b_data_ = std::make_pair(0, nullptr);
        c_data_ = std::make_pair(0, nullptr);
    }

    ~MemoryPoolGPU() {
        if (a_data_.second != nullptr) {
            deallocateDeviceMemory(a_data_.second);
            a_data_.second = nullptr;
            a_data_.first = 0;
        }
        if (b_data_.second != nullptr) {
            deallocateDeviceMemory(b_data_.second);
            b_data_.second = nullptr;
            b_data_.first = 0;
        }
        if (c_data_.second != nullptr) {
            deallocateDeviceMemory(c_data_.second);
            c_data_.second = nullptr;
            c_data_.first = 0;
        }
    }

    void *getAllocatedDataA(size_t size) {
        if (a_data_.first < size) {
            if (a_data_.second != nullptr) {
                deallocateDeviceMemory(a_data_.second);
            }
            allocateDeviceMemory(&a_data_.second, size);
            a_data_.first = size;
        }
        return a_data_.second;
    }

    void *getAllocatedDataB(size_t size) {
        if (b_data_.first < size) {
            if (b_data_.second != nullptr) {
                deallocateDeviceMemory(b_data_.second);
            }
            allocateDeviceMemory(&b_data_.second, size);
            b_data_.first = size;
        }
        return b_data_.second;
    }

    void *getAllocatedDataC(size_t size) {
        if (c_data_.first < size) {
            if (c_data_.second != nullptr) {
                deallocateDeviceMemory(c_data_.second);
            }
            allocateDeviceMemory(&c_data_.second, size);
            c_data_.first = size;
        }
        return c_data_.second;
    }
};

} // namespace hem
