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

/* If building static, make EVI_API empty. You can set EVI_STATIC from CMake if needed. */

#if defined(_WIN32) || defined(__CYGWIN__)
#if defined(EVI_BUILDING_LIB)
#define EVI_API __declspec(dllexport)
#else
#define EVI_API __declspec(dllimport)
#endif
#else
#define EVI_API __attribute__((visibility("default")))
#endif
