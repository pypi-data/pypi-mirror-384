////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2021-2024, CryptoLab Inc. All rights reserved.               //
//                                                                            //
// This software and/or source code may be commercially used and/or           //
// disseminated only with the written permission of CryptoLab Inc,            //
// or in accordance with the terms and conditions stipulated in the           //
// agreement/contract under which the software and/or source code has been    //
// supplied by CryptoLab Inc. Any unauthorized commercial use and/or          //
// dissemination of this file is strictly prohibited and will constitute      //
// an infringement of copyright.                                              //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <cstdint>

namespace evi {

constexpr uint64_t DEGREE = 4096;

constexpr int MIN_CONTEXT_SIZE_LOG = 5;
constexpr int MAX_CONTEXT_SIZE_LOG = 12;
constexpr int MIN_CONTEXT_SIZE = 1 << MIN_CONTEXT_SIZE_LOG;
constexpr int MAX_CONTEXT_SIZE = 1 << MAX_CONTEXT_SIZE_LOG;
constexpr int NUM_CONTEXT = MAX_CONTEXT_SIZE_LOG - MIN_CONTEXT_SIZE_LOG + 1;

} // namespace evi
