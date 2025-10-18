////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/device/Device.hpp"
#include <cstddef>
#include <vector>

namespace hem {

struct ModulusPack {
    u64 modulus = 0;
    u64 barr_for_64 = 0;
    u64 two_to_64 = 0;
    u64 two_to_64_shoup = 0;
};

class ModulusEngineUnit {
public:
    ModulusEngineUnit() = delete;
    ModulusEngineUnit(const Device &device);
    ModulusEngineUnit(const Device &device, u64 modulus);

    ~ModulusEngineUnit();

    ModulusEngineUnit(const ModulusEngineUnit &);
    ModulusEngineUnit &operator=(const ModulusEngineUnit &);
    ModulusEngineUnit(ModulusEngineUnit &&) noexcept;
    ModulusEngineUnit &operator=(ModulusEngineUnit &&) noexcept;

    void initialize(u64 modulus);

    const Device &getDevice() const { return device_; }
    const ModulusPack &getModulusPackHost() const { return modulus_pack_host_; }
    const ModulusPack *getModulusPackDevicePtr() const {
        return modulus_pack_device_ptr_;
    }

private:
    void allocateDevicePtrAndCopyToDeviceIfDevice();
    void deallocateDevicePtrIfDevice();

    // TODO: allow multiple devices.
    const Device device_;
    ModulusPack modulus_pack_host_;

    // modulus_pack_device_ptr_ is a copy of modulus_pack_host_ on the device.
    ModulusPack *modulus_pack_device_ptr_ = nullptr;
};

class ModulusEngine {
public:
    ModulusEngine() = delete;
    ModulusEngine(const Device &device);
    ModulusEngine(const Device &device, const std::vector<u64> &moduli);
    ~ModulusEngine();
    ModulusEngine(const ModulusEngine &);
    ModulusEngine &operator=(const ModulusEngine &);
    ModulusEngine(ModulusEngine &&) noexcept;
    ModulusEngine &operator=(ModulusEngine &&) noexcept;

    void initialize(const std::vector<u64> &moduli);

    const ModulusEngineUnit &getModulusEngineUnit(size_t level) const {
        return modulus_engine_units_[level];
    }

    const Device &getDevice() const { return device_; }

private:
    const Device device_;
    std::vector<ModulusEngineUnit> modulus_engine_units_;
};

} // namespace hem
