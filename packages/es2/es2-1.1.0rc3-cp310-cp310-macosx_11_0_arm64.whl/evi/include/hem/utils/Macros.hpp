////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <iostream>
#include <type_traits>

#define UNUSED(x) (void)(x)

#define CEIL(M, N) (((M) + (N)-1) / (N))

template <typename... Args>
constexpr void UNUSED_ALL([[maybe_unused]] Args &&...args) noexcept {
    (void)sizeof...(Args); // consumes them, safe if none
}

template <typename T>
struct is_64bit_integer_type
    : std::bool_constant<
          std::is_same_v<std::remove_cv_t<std::remove_reference_t<T>>,
                         int64_t> ||
          std::is_same_v<std::remove_cv_t<std::remove_reference_t<T>>,
                         uint64_t>> {};

template <typename T>
inline constexpr bool is_64bit_integer_type_v = is_64bit_integer_type<T>::value;
inline constexpr bool isAVXactivated() noexcept {
#ifdef HEM_AVX512DQ
    return true;
#elif defined(HEM_AVX2)
    return true;
#else
    return false;
#endif
}

#define NOT_SUPPORTED_FUNCTION()                                               \
    throw std::runtime_error("Cannot support the function '" +                 \
                             std::string(__func__) +                           \
                             "' in the current build configuration");

#if defined(HEM_USE_CUDA)

#ifdef __CUDACC__
#define CUDA_CALLABLE __device__
#define CUDA_CALLABLE_INLINE __inline__ __device__
#else
#define CUDA_CALLABLE
#define CUDA_CALLABLE_INLINE inline
#endif

#define CHECK_CUBLAS(call)                                                     \
    {                                                                          \
        const cublasStatus_t status = call;                                    \
        if (status != CUBLAS_STATUS_SUCCESS) {                                 \
            std::cerr << "CUBLAS Error: " << __FILE__ << ":" << __LINE__       \
                      << ", status: " << status << "\n";                       \
            exit(1);                                                           \
        }                                                                      \
    }

#define CHECK_CUDA(call)                                                       \
    {                                                                          \
        const cudaError_t error = call;                                        \
        if (error != cudaSuccess) {                                            \
            std::cerr << "Error: " << __FILE__ << ":" << __LINE__ << ", ";     \
            std::cerr << "code: " << error                                     \
                      << ", reason: " << cudaGetErrorString(error) << "\n";    \
            exit(1);                                                           \
        }                                                                      \
    }
#elif defined(HEM_USE_HIP)

#define CUDA_CALLABLE __host__ __device__
#define CUDA_CALLABLE_INLINE __inline__ __host__ __device__

#define CHECK_CUBLAS(call)                                                     \
    {                                                                          \
        const hipblasStatus_t status = call;                                   \
        if (status != HIPBLAS_STATUS_SUCCESS) {                                \
            std::cerr << "HIPBLAS Error: " << __FILE__ << ":" << __LINE__      \
                      << ", status: " << status << "\n";                       \
            exit(1);                                                           \
        }                                                                      \
    }

#define CHECK_CUDA(call)                                                       \
    {                                                                          \
        const hipError_t error = call;                                         \
        if (error != hipSuccess) {                                             \
            std::cerr << "Error: " << __FILE__ << ":" << __LINE__ << ", ";     \
            std::cerr << "code: " << error                                     \
                      << ", reason: " << hipGetErrorString(error) << "\n";     \
            exit(1);                                                           \
        }                                                                      \
    }
#endif

// https://gcc.gnu.org/onlinedocs/cpp/Common-Predefined-Macros.html
#define GCC_VERSION                                                            \
    (__GNUC__ * 10000 + __GNUC_MINOR__ * 100 + __GNUC_PATCHLEVEL__)

#define TO_STRING_HELPER(X) #X
#define TO_STRING(X) TO_STRING_HELPER(X)

#if defined(__clang__)
#define LOOP_UNROLL_2 _Pragma("clang loop unroll_count(2)")
#define LOOP_UNROLL_4 _Pragma("clang loop unroll_count(4)")
#define LOOP_UNROLL_8 _Pragma("clang loop unroll_count(8)")
#define LOOP_UNROLL(n) _Pragma(TO_STRING(clang loop unroll_count(n)))
#elif defined(__GNUG__) && GCC_VERSION > 80000 && !defined(__NVCC__)
#define LOOP_UNROLL_2 _Pragma("GCC unroll 2")
#define LOOP_UNROLL_4 _Pragma("GCC unroll 4")
#define LOOP_UNROLL_8 _Pragma("GCC unroll 8")
#define LOOP_UNROLL(n) _Pragma(TO_STRING(GCC unroll(n)))
#else
#define LOOP_UNROLL_2
#define LOOP_UNROLL_4
#define LOOP_UNROLL_8
#define LOOP_UNROLL(n)
#endif

#ifdef HEM_USE_OPENMP
#define OMP_PRAGMA(x) _Pragma(#x)
#define OMP_PAR_FOR        OMP_PRAGMA(omp parallel for)
#else
#define OMP_PRAGMA(x)
#define OMP_PAR_FOR
#endif
