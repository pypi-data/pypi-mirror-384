////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2023 Crypto Lab Inc.                                    //
//                                                                            //
// - This file is part of HEaaN homomorphic encryption library.               //
// - HEaaN cannot be copied and/or distributed without the express permission //
//  of Crypto Lab Inc.                                                        //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <memory>
#include <string>
#include <vector>

#include "HEaaN/HEaaNExport.hpp"
#include "HEaaN/Integers.hpp"
#include "HEaaN/LWE/ParameterPreset.hpp"
#include "HEaaN/Real.hpp"
#include "HEaaN/SecurityLevel.hpp"
#include "HEaaN/device/Device.hpp"

namespace HEaaN::LWE {

class ContextContent;
using Context = std::shared_ptr<ContextContent>;

///@brief Make a context object based on a given parameter preset
///@param[in] preset Parameter preset
///@param[in] cuda_device_ids Optional CUDA device IDs to be used. You can use
/// only the specified cuda devices with this Context.
///@returns The context object generated from the predetermined parameters in
/// the given ParameterPreset.
///@throws RuntimeException if one calls this function with
/// preset == ParameterPreset::CUSTOM.  In order to make sense, one must use
/// the other overloaded `makeContext()` function to specify custom parameters
/// explicitly.
HEAAN_API Context makeContext(const ParameterPreset &preset,
                              const CudaDeviceIds &cuda_device_ids = {});

///@brief Make a context based on custom parameters
///@param[in] dimension This is the dimension of the vector space (Z_Q)^N
///@param[in] chain_length This is the number of primes in the RNS decomposition
/// of each vector constituting the ciphertexts or the keys in the current
/// homomorphic encryption context.  There are the base prime (the prime at
/// level 0) and the quantization primes at the higher levels, so chain_length
/// is equal to the sum of the number of base primes (usually this number is 1)
/// and the number of quantization primes.  The value must be <= 50.
///@param[in] bpsize The size of the base prime in bits.  The value must be
/// greater than or equal to qpsize, less than or equal to 61.
///@param[in] qpsize The size of the quantization primes in bits.  The value
/// must be greater than or equal to 36, less than or equal to bpsize.
///@param[in] cuda_device_ids Optional CUDA device IDs to be used. You can use
/// only the specified cuda devices with this Context.
///@returns The context object generated from the input parameters.
HEAAN_API Context makeContext(const u64 dimension, const u64 chain_length,
                              const u64 bpsize, const u64 qpsize,
                              const CudaDeviceIds &cuda_device_ids = {});

///@brief Make a context object from a "context file"
///@param[in] filename It designates the path of the file to be read inside
/// this function.
///@param[in] cuda_device_ids Optional CUDA device IDs to be used. You can use
/// only the specified cuda devices with this Context.
///@returns The generated context object.
///@details A context file is one created by `saveContextToFile`.
///@throws RuntimeException if it fails to open `filename` in read mode.
HEAAN_API Context makeContextFromFile(
    const std::string &filename, const CudaDeviceIds &cuda_device_ids = {});

///@brief Save a context object into a file.
///@param[in] context A context object to be saved.
///@param[in] filename File path to be written.
///@throws RuntimeException if it fails to open `filename` in write mode.
HEAAN_API void saveContextToFile(const Context &context,
                                 const std::string &filename);

///@brief Get the dimension of the ax part vector of a ciphertext
///@param[in] context
HEAAN_API u64 getDimension(const Context &context);

///@brief Get the level of a fresh ciphertext, which is the maximum level that
/// users can encrypt a ciphertext to.
///@param[in] context
HEAAN_API u64 getEncryptionLevel(const Context &context);

///@brief Get the default list of scale factors
///@param[in] context
///@details The i-th element corresponds to level i. HEaaN uses fixed scale
/// factor system, which fixes the scale factor with respect to each level.
/// It helps managing scale factor properly, and saves some level.
HEAAN_API std::vector<Real> getDefaultScaleFactorList(const Context &context);

///@brief Get the list of primes
///@param[in] context
///@details The i-th element corresponds to level i
HEAAN_API std::vector<u64> getPrimeList(const Context &context);

///@brief Get the security level of the given context
///@param[in] context Context object
///@details The security level is
/// chosen according to the [homomorphic encryption standard
/// documentation](http://homomorphicencryption.org/wp-content/uploads/2018/11/HomomorphicEncryptionStandardv1.1.pdf),
/// Table 1, distribution (-1,1) (ternary uniform with elements -1, 0 and 1) and
/// CryptoLab's own [experimental
/// results](https://deciduous-cause-137.notion.site/Security-Level-of-Parameters-3ecb6810c57843e4b55e788f34b36108).
///@returns The security level as described in HEaaN::SecurityLevel
HEAAN_API SecurityLevel getSecurityLevel(const Context &context);

} // namespace HEaaN::LWE
