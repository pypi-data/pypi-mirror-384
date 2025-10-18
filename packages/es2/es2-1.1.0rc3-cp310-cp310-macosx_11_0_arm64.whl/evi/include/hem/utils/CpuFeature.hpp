////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once
// TODO: Remove this file and make another file for HEM.
// This file is a copy of the original file from HEAAN library.
// The original file is located at HEAAN/include/HEAAN/impl/CpuFeature.hpp.

#include "hem/DataType.hpp"

namespace HEaaN {

using CpuFeatureSet = hem::u64;

enum class CpuFeature : hem::u64 {
    AVX2 = 1 << 0,
    AVX512DQ = 1 << 1,
    AVX512F = 1 << 2,
    AVX512VL = 1 << 3
};

// Call cpuid functions and return a `FeatureSet` where each bit corresponds to
// a `Feature`
// XXX(wk): each time we call cpuid instructions multiple times. Should we cache
// the return value per thread?
CpuFeatureSet getCurrentFeature();

inline bool hasCPUFeature(CpuFeature feature) {
    return getCurrentFeature() & static_cast<hem::u64>(feature);
}

} // namespace HEaaN
