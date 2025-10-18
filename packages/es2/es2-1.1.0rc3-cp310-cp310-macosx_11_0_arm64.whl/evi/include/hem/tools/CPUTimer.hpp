////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

#include <chrono>

class CPUTimer {
public:
    CPUTimer() = default;

    void startTimer() { start_ = std::chrono::system_clock::now(); }

    float stopTimer() {
        stop_ = std::chrono::system_clock::now();
        elapsed_time_ = static_cast<float>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(stop_ - start_)
                .count());
        return elapsed_time_ / 1000000;
    }

private:
    std::chrono::system_clock::time_point start_, stop_;
    float elapsed_time_;
};
