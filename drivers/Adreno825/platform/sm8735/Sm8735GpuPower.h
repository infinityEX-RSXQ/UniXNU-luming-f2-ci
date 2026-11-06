/* SPDX-License-Identifier: MIT */
#ifndef SM8735_GPU_POWER_H
#define SM8735_GPU_POWER_H

#include <stdint.h>

/*
 * Minimal SM8735 GPU power bring-up.
 *
 * SurveyRead() is read-only and safe for first hardware probing.
 * EnableCxGdsc() writes only the GPUCC CX GDSC block (the offset matches the
 * A830/SM8750 layout); it does not touch PLL, RPMh, SMMU, GMU or CP.
 */

#ifdef __cplusplus
extern "C" {
#endif

typedef struct Sm8735GpuPowerIo {
    void *cookie;
    int (*read32)(void *cookie, uint64_t phys, uint32_t *value);
    int (*write32)(void *cookie, uint64_t phys, uint32_t value);
    int (*delay_us)(void *cookie, unsigned microseconds);
} Sm8735GpuPowerIo;

typedef struct Sm8735GpuPowerSurvey {
    uint32_t ok;                 /* non-zero only when every read succeeded */
    uint32_t pll0_mode;          /* GPUCC + 0x00 */
    uint32_t pll0_l;             /* GPUCC + 0x10 */
    uint32_t pll0_config;        /* GPUCC + 0x20 */
    uint32_t cx_bcr;             /* GPUCC + 0x907c */
    uint32_t cx_gdscr;           /* GPUCC + 0x9080 */
    uint32_t cx_cfg_gdscr;       /* GPUCC + 0x9084 */
    uint32_t cx_gds_hw_ctrl;     /* GPUCC + 0x9094 */
    uint32_t gmu_bcr;            /* GPUCC + 0x9314 */
    uint32_t gmu_rcg;            /* GPUCC + 0x9318 */
    uint32_t hub_rcg;            /* GPUCC + 0x93ec */
    uint32_t gx_clkctl;          /* 0x3d68024 */
    uint32_t gpu_id0;            /* GPU + 0x000 */
    uint32_t gpu_id4;            /* GPU + 0x004 */
    uint32_t gpu_id100;          /* GPU + 0x100 */
    uint32_t cx_powered;         /* 1 when CxGdsHwCtrl.PWR_ON is set */
    uint32_t gpu_id_candidate;   /* first non-zero/non-0xffffffff of the three */
} Sm8735GpuPowerSurvey;

typedef enum Sm8735GpuPowerStatus {
    Sm8735GpuPowerOk = 0,
    Sm8735GpuPowerIoError,
    Sm8735GpuPowerUnexpectedState,
    Sm8735GpuPowerTimeout,
} Sm8735GpuPowerStatus;

typedef struct Sm8735GpuPowerTrace {
    uint64_t offset;             /* last register touched */
    uint32_t value;              /* last value written/read */
    uint32_t reads, writes;
} Sm8735GpuPowerTrace;

/* Read-only. Returns 0 when every register was read, -1 otherwise; out->ok is set. */
int Sm8735GpuPowerSurveyRead(const Sm8735GpuPowerIo *io, Sm8735GpuPowerSurvey *out);

/* Pure helper for host tests: choose the first plausible GPU ID word. */
uint32_t Sm8735GpuPowerChooseId(uint32_t id0, uint32_t id4, uint32_t id100);

/*
 * Conservative CX GDSC enable: update(CxGdscr, 0xfff007, 0x228000), wait 1 us,
 * poll CxGdsHwCtrl.PWR_ON for at most 2000 us, then set RETAIN_FF.
 * No PLL, no RPMh, no SMMU, no GMU.
 */
Sm8735GpuPowerStatus Sm8735GpuPowerEnableCxGdsc(const Sm8735GpuPowerIo *io,
    Sm8735GpuPowerTrace *trace);

/*
 * GPU_CC_PLL0 programming with the values embedded in the stock gpucc-tuna.ko
 * (gpu_cc_pll0_config: L 0x34, alpha 0x1555, config 0x20485699/0x00182261/0x82aa299c,
 * user 4/5). This is still NOT called by the kernel: the PLL is shared with the
 * boot chain and the field mapping must be confirmed first.
 */
Sm8735GpuPowerStatus Sm8735GpuPowerProgramPll(const Sm8735GpuPowerIo *io,
    Sm8735GpuPowerTrace *trace);

#ifdef __cplusplus
}
#endif

#endif /* SM8735_GPU_POWER_H */
