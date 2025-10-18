/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2022
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Nikolaos Papandreou
 *                Milos Stanisavljevic
 *                Jan van Lunteren
 *
 * End Copyright
 ********************************************************************/

#ifndef SIMD_DEFINES
#define SIMD_DEFINES

#ifdef Z14_SIMD
#ifdef WITH_ZOS
#include <zos_wrappers/builtins.h>
#else
#include <vecintrin.h>
#endif
#define CACHE_LINE_SIZE 256
#define PAR_COUNT       4
#elif defined(POWER_VMX)
#include <altivec.h>
#define CACHE_LINE_SIZE 64
#define PAR_COUNT       8
#elif defined(X86_AVX512)
#include <immintrin.h>
#define CACHE_LINE_SIZE 64
#define PAR_COUNT       16
#elif defined(X86_AVX2)
#include <immintrin.h>
#define CACHE_LINE_SIZE 64
#define PAR_COUNT       8
#else
#define CACHE_LINE_SIZE 64
#define PAR_COUNT       1
#endif

#endif
