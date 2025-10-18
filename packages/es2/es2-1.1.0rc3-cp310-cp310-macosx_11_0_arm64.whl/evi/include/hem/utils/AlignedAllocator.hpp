////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <cstddef>
#include <cstdlib>
#include <limits>
#include <new>
#include <utility>
#include <vector>

namespace hem {

#ifndef SIZE_MAX
#ifdef __SIZE_MAX__
#define SIZE_MAX __SIZE_MAX__
#else
#define SIZE_MAX std::numeric_limits<size_t>::max()
#endif
#endif

#ifdef __cpp_lib_hardware_interference_size
using std::hardware_constructive_interference_size;
using std::hardware_destructive_interference_size;
#else
// 64 bytes on x86-64 │ L1_CACHE_BYTES │ L1_CACHE_SHIFT │ __cacheline_aligned
constexpr std::size_t hardware_constructive_interference_size = 64;
constexpr std::size_t hardware_destructive_interference_size = 64;
#endif

#if defined(HEM_AVX512DQ)
constexpr std::size_t DEFAULT_ALIGNMENT_BASE = 64;
#elif defined(HEM_AVX2)
constexpr std::size_t DEFAULT_ALIGNMENT_BASE = 32;
#else
constexpr std::size_t DEFAULT_ALIGNMENT_BASE = 16;
#endif

constexpr std::size_t DEFAULT_ALIGNMENT =
    (DEFAULT_ALIGNMENT_BASE > hardware_destructive_interference_size)
        ? DEFAULT_ALIGNMENT_BASE
        : hardware_destructive_interference_size;

template <class T, std::size_t alignment = DEFAULT_ALIGNMENT>
struct AlignedAllocator {
    static_assert((alignment & (alignment - 1)) == 0,
                  "alignment must be power of two");
    static_assert(alignment >= alignof(T), "alignment must be >= alignof(T)");

    using value_type = T;
    using is_always_equal = std::true_type;

    AlignedAllocator() noexcept = default;

    T *allocate(std::size_t n) {
        if (n > SIZE_MAX / sizeof(T))
            throw std::bad_array_new_length{};
        const auto size = (n + alignment - 1) / alignment * alignment;
        void *p = ::operator new(size * sizeof(T), std::align_val_t(alignment));
        if (p == nullptr)
            throw std::bad_alloc();
        return static_cast<T *>(p);
    }
    void deallocate(T *p, [[maybe_unused]] std::size_t n) noexcept {
        ::operator delete(p, std::align_val_t(alignment));
    }

    template <class U> struct rebind {
        using other = AlignedAllocator<U, alignment>;
    };
};

} // namespace hem
