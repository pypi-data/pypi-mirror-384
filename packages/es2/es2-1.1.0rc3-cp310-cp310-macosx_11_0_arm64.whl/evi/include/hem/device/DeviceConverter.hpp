////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "HEaaN/device/Device.hpp"
#include "hem/device/Device.hpp"
#include <stdexcept>

namespace hem {

inline hem::Device convertDevice(const HEaaN::Device &device) {
    switch (device.type()) {
    case HEaaN::DeviceType::CPU:
        return hem::Device(hem::DeviceType::CPU); // NOLINT
    case HEaaN::DeviceType::GPU:
        return hem::Device(hem::DeviceType::GPU, device.id());
    default:
        throw std::invalid_argument("Unsupported device type.");
    }
}

inline HEaaN::Device convertDevice(const hem::Device &device) {
    switch (device.type()) {
    case hem::DeviceType::CPU:
        return HEaaN::Device(HEaaN::DeviceType::CPU); // NOLINT
    case hem::DeviceType::GPU:
        return HEaaN::Device(HEaaN::DeviceType::GPU, device.id());
    default:
        throw std::invalid_argument("Unsupported device type.");
    }
}

} // namespace hem
