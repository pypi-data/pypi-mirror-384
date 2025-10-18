////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// Copyright (C) 2024-2025 CryptoLab, Inc. All rights reserved.               //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#pragma once

namespace hem {

enum hemOrder_t {
    hemRowMajor = 101,
    hemColMajor = 102,
};

enum hemOperation_t {
    hemNoTrans = 111,
    hemTrans = 112,
};

enum hemNative_t {
    NONE = 91,
    TILED = 92,
};

inline hemOrder_t convertTransToOrder(hemOrder_t order, hemOperation_t trans) {
    if (order == hemRowMajor) {
        if (trans == hemNoTrans)
            return hemRowMajor;
        else
            return hemColMajor;
    } else {
        if (trans == hemNoTrans)
            return hemColMajor;
        else
            return hemRowMajor;
    }
}

inline hemOperation_t convertOrderToTrans(hemOrder_t order1,
                                          hemOrder_t order2) {
    if (order1 == order2)
        return hemNoTrans;
    else
        return hemTrans;
}

} // namespace hem
