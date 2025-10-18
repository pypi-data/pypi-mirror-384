////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <limits>
#include <stdexcept>
#include <type_traits>

namespace hem {
namespace utils {

// Safe cast from unsigned to signed integer
template <typename To, typename From>
typename std::enable_if_t<std::is_integral_v<To> && std::is_integral_v<From> &&
                              std::is_signed_v<To> && std::is_unsigned_v<From>,
                          To>
safe_cast(From value) {
    constexpr auto max_signed = static_cast<typename std::make_unsigned_t<To>>(
        std::numeric_limits<To>::max());

    if (value > max_signed) {
        throw std::overflow_error("Value too large for target signed type");
    }
    return static_cast<To>(value);
}

// Safe cast from signed to unsigned integer
template <typename To, typename From>
typename std::enable_if_t<std::is_integral_v<To> && std::is_integral_v<From> &&
                              std::is_unsigned_v<To> && std::is_signed_v<From>,
                          To>
safe_cast(From value) {
    if (value < 0) {
        throw std::underflow_error(
            "Negative value cannot be cast to unsigned type");
    }

    constexpr auto max_unsigned = std::numeric_limits<To>::max();
    if (static_cast<typename std::make_unsigned_t<From>>(value) >
        max_unsigned) {
        throw std::overflow_error("Value too large for target unsigned type");
    }
    return static_cast<To>(value);
}

// Safe multiplication with overflow check
template <typename T>
typename std::enable_if_t<std::is_integral_v<T>, T> safe_multiply(T a, T b) {
    if (a == 0 || b == 0)
        return 0;

    constexpr T max_val = std::numeric_limits<T>::max();

    if (a > 0 && b > 0) {
        if (a > max_val / b) {
            throw std::overflow_error("Multiplication overflow");
        }
    } else if (a < 0 && b < 0) {
        if (a < max_val / b) {
            throw std::overflow_error("Multiplication overflow");
        }
    } else {
        // One positive, one negative
        constexpr T min_val = std::numeric_limits<T>::min();
        if ((a > 0 && b < min_val / a) || (b > 0 && a < min_val / b)) {
            throw std::underflow_error("Multiplication underflow");
        }
    }

    return a * b;
}

// Safe modular reduction
template <typename T>
typename std::enable_if_t<std::is_integral_v<T> && std::is_unsigned_v<T>, T>
safe_mod_reduce(T value, T modulus) {
    if (modulus == 0) {
        throw std::invalid_argument("Modulus cannot be zero");
    }
    return value % modulus;
}

} // namespace utils
} // namespace hem
