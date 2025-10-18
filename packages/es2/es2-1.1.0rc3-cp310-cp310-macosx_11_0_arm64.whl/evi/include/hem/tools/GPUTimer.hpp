////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#if defined(HEM_USE_CUDA)

#include <cuda_runtime_api.h>
#include <driver_types.h>
#include <iostream>

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

class GPUTimer {
public:
    GPUTimer() {
        CHECK_CUDA(cudaEventCreate(&start_));
        CHECK_CUDA(cudaEventCreate(&stop_));
    }

    ~GPUTimer() {
        CHECK_CUDA(cudaEventDestroy(start_));
        CHECK_CUDA(cudaEventDestroy(stop_));
    }

    void startTimer() { CHECK_CUDA(cudaEventRecord(start_, nullptr)); }

    float stopTimer() {
        CHECK_CUDA(cudaEventRecord(stop_, nullptr));
        CHECK_CUDA(cudaEventSynchronize(stop_));
        CHECK_CUDA(cudaEventElapsedTime(&elapsed_time_, start_, stop_));
        return elapsed_time_;
    }

private:
    cudaEvent_t start_, stop_;
    float elapsed_time_;
};

#elif defined(HEM_USE_HIP)

#include <hip/hip_runtime.h>
#include <iostream>

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

class GPUTimer {
public:
    GPUTimer() {
        CHECK_CUDA(hipEventCreate(&start_));
        CHECK_CUDA(hipEventCreate(&stop_));
    }

    ~GPUTimer() {
        CHECK_CUDA(hipEventDestroy(start_));
        CHECK_CUDA(hipEventDestroy(stop_));
    }

    void startTimer() { CHECK_CUDA(hipEventRecord(start_, nullptr)); }

    float stopTimer() {
        CHECK_CUDA(hipEventRecord(stop_, nullptr));
        CHECK_CUDA(hipEventSynchronize(stop_));
        CHECK_CUDA(hipEventElapsedTime(&elapsed_time_, start_, stop_));
        return elapsed_time_;
    }

private:
    hipEvent_t start_, stop_;
    float elapsed_time_;
};

#endif
