////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include "hem/DataType.hpp"
#include "hem/ModulusMatrix.hpp"
#include "hem/RawArray.hpp"

namespace hem {

void encodeMatrix(const RawArray<double> &input, PTMatrix<i64> &output,
                  double scale_factor);

void encodeMatrix(const RawArray<double> &input, PTMatrix<u64> &output,
                  double scale_factor);

} // namespace hem
