////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <cstddef>

namespace hem {

void allocateDeviceMemory(void **ptr, size_t size);

void deallocateDeviceMemory(void *ptr);

void memcpyHostToDeviceMemory(void *dst, const void *src, size_t size);

void memcpyDeviceToHostMemory(void *dst, const void *src, size_t size);

void memcpyDeviceToDeviceMemory(void *dst, const void *src, size_t size);

void memsetDeviceMemory(void *dst, int value, size_t size);

} // namespace hem
