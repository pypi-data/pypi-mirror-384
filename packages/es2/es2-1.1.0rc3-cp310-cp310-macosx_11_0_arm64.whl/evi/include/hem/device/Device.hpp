////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

namespace hem {

enum class DeviceType {
    CPU,
    GPU,
    // Add other device types as needed
};

class Device {
public:
    constexpr Device(DeviceType device_type)
        : device_type_(device_type), device_id_(0) {}
    constexpr explicit Device(DeviceType device_type, int device_id)
        : device_type_(device_type), device_id_(device_id) {}

    constexpr DeviceType type() const { return device_type_; }
    constexpr int id() const { return device_id_; }
    constexpr bool isCPU() const { return device_type_ == DeviceType::CPU; }
    constexpr bool isGPU() const { return device_type_ == DeviceType::GPU; }

    constexpr bool operator==(const Device &other) const {
        return device_type_ == other.device_type_ &&
               device_id_ == other.device_id_;
    }
    constexpr bool operator!=(const Device &other) const {
        return !(*this == other);
    }
    constexpr bool operator<(const Device &other) const {
        return device_type_ < other.device_type_ ||
               (device_type_ == other.device_type_ &&
                device_id_ < other.device_id_);
    }

private:
    DeviceType device_type_;
    int device_id_;
};

} // namespace hem
