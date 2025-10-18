/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Nikolas Ioannou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_HOST_SOLVER_UTIL_HH_
#define GLM_HOST_SOLVER_UTIL_HH_
#include <cstdlib>
#include <cstdio>

namespace glm {

#define is_power_of_two(x) ((0 < (x)) && (0 == ((x) & ((x)-1))))
#define unlikely(x)        __builtin_expect((x), 0)

#ifdef WITH_VS
#define cpu_malloc(_SIZE, _ALIGN, _typeof) ((_typeof*)_aligned_malloc((_SIZE), (_ALIGN)));
#define cpu_free(_ptr)                     _aligned_free((void*)(_ptr))
#elif WITH_ZOS
#define cpu_malloc(_SIZE, _ALIGN, _typeof) ((_typeof*)malloc((_SIZE)));
#define cpu_free(_ptr)                     free(_ptr)
#else
#define cpu_malloc(_SIZE, _ALIGN, _typeof)                                                                             \
    ({                                                                                                                 \
        void* _ptr = NULL;                                                                                             \
        int   rc   = posix_memalign(&_ptr, (_ALIGN), (_SIZE));                                                         \
        if (0 != rc) {                                                                                                 \
            _ptr = NULL;                                                                                               \
        }                                                                                                              \
        (_typeof*)_ptr;                                                                                                \
    })
#define cpu_free(_ptr) free(_ptr)
#endif

static inline uint32_t udiv_round_up(const uint32_t dividend, const uint32_t divisor)
{
    return 0UL != divisor ? (dividend + divisor - 1U) / divisor : 1U;
}

static inline uint32_t uceil_up(const uint32_t val, const uint32_t divisor)
{
    return divisor * udiv_round_up(val, divisor);
}

static inline uint32_t align_up(const uint32_t val, const uint32_t alignment) { return uceil_up(val, alignment); }

static inline uint32_t align_down(const uint32_t val, const uint32_t alignment)
{
    return 0ULL != alignment ? val / alignment * alignment : 0ULL;
}

static constexpr uint32_t _MIN_L1_CACHE_LINE_SIZE = 32;
static constexpr uint32_t _MAX_L1_CACHE_LINE_SIZE = 128;
static uint32_t           cpu_l1d_cache_line_size()
{
    uint32_t    cache_line_size = 64, input = 0;
    FILE* const f = fopen("/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size", "r");
    if (nullptr == f)
        return cache_line_size;
    const int n = fscanf(f, "%u", &input);
    if (1 == n && is_power_of_two(input) && _MIN_L1_CACHE_LINE_SIZE <= input && input <= _MAX_L1_CACHE_LINE_SIZE) {
        cache_line_size = input;
    }
    fclose(f);
    return cache_line_size;
}

};
#endif // GLM_HOST_SOLVER_UTIL_HH_
