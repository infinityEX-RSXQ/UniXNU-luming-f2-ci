/* SPDX-License-Identifier: MIT */
/* [measured] stock luming vendor_boot.dtb: qcom,gpu-pwrlevel-bins.
 * Regenerate from the DTB, do not hand-edit. GMU level = index + 1. */
#ifndef SM8735_GPU_PWRLEVELS_H
#define SM8735_GPU_PWRLEVELS_H
#include "Adreno830Board.h"

#define SM8735_GPU_BIN_COUNT 3u
#define SM8735_GPU_COMMON_LEVEL_COUNT 8u   /* ascending prefix shared by all three bins */

/* bin 0: speed-bin 0, initial level 10, 11 levels */
static const Adreno830Level sm8735_levels_0[11] = {
    {264000u, 0x38u, 1u, 1u, 3u, 0u, 0xc8295ffdu},
    {362000u, 0x40u, 1u, 3u, 3u, 0u, 0xc8295ffdu},
    {510000u, 0x80u, 2u, 6u, 6u, 0u, 0xc02c5ffdu},
    {644000u, 0xc0u, 4u, 6u, 7u, 0u, 0xa82b5ffdu},
    {688000u, 0xe0u, 4u, 6u, 7u, 0u, 0x882b5ffdu},
    {763000u, 0x100u, 7u, 8u, 9u, 0u, 0x882b5ffdu},
    {873000u, 0x140u, 7u, 10u, 11u, 0u, 0xa82a5ffdu},
    {937000u, 0x180u, 9u, 10u, 11u, 0u, 0x882a5ffdu},
    {1050000u, 0x190u, 11u, 11u, 11u, 0u, 0x882a5ffdu},
    {1100000u, 0x1a0u, 11u, 11u, 11u, 0u, 0x88295ffdu},
    {1150000u, 0x1b0u, 11u, 11u, 11u, 0u, 0xa8285ffdu},
};

/* bin 1: speed-bin 216, initial level 8, 9 levels */
static const Adreno830Level sm8735_levels_1[9] = {
    {264000u, 0x38u, 1u, 1u, 3u, 0u, 0xc8295ffdu},
    {362000u, 0x40u, 1u, 3u, 3u, 0u, 0xc8295ffdu},
    {510000u, 0x80u, 2u, 6u, 6u, 0u, 0xc02c5ffdu},
    {644000u, 0xc0u, 4u, 6u, 7u, 0u, 0xa82b5ffdu},
    {688000u, 0xe0u, 4u, 6u, 7u, 0u, 0x882b5ffdu},
    {763000u, 0x100u, 7u, 8u, 9u, 0u, 0x882b5ffdu},
    {873000u, 0x140u, 7u, 10u, 11u, 0u, 0xa82a5ffdu},
    {937000u, 0x180u, 9u, 10u, 11u, 0u, 0x882a5ffdu},
    {1025000u, 0x1a0u, 11u, 11u, 11u, 0u, 0x88295ffdu},
};

/* bin 2: speed-bin 242, initial level 10, 11 levels */
static const Adreno830Level sm8735_levels_2[11] = {
    {264000u, 0x38u, 1u, 1u, 3u, 0u, 0xc8295ffdu},
    {362000u, 0x40u, 1u, 3u, 3u, 0u, 0xc8295ffdu},
    {510000u, 0x80u, 2u, 6u, 6u, 0u, 0xc02c5ffdu},
    {644000u, 0xc0u, 4u, 6u, 7u, 0u, 0xa82b5ffdu},
    {688000u, 0xe0u, 4u, 6u, 7u, 0u, 0x882b5ffdu},
    {763000u, 0x100u, 7u, 8u, 9u, 0u, 0x882b5ffdu},
    {873000u, 0x140u, 7u, 10u, 11u, 0u, 0xa82a5ffdu},
    {937000u, 0x180u, 9u, 10u, 11u, 0u, 0x882a5ffdu},
    {1050000u, 0x190u, 11u, 11u, 11u, 0u, 0x882a5ffdu},
    {1100000u, 0x1a0u, 11u, 11u, 11u, 0u, 0x88295ffdu},
    {1150000u, 0x1b0u, 11u, 11u, 11u, 0u, 0xa8285ffdu},
};

static const struct Sm8735GpuBin {
    const Adreno830Level *levels;
    uint8_t count, initial;
    uint32_t speed;
} sm8735_gpu_bins[SM8735_GPU_BIN_COUNT] = {
    {sm8735_levels_0, 11u, 10u, 0u},
    {sm8735_levels_1, 9u, 8u, 216u},
    {sm8735_levels_2, 11u, 10u, 242u},
};

#endif /* SM8735_GPU_PWRLEVELS_H */
